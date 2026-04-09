'use strict';

const { Contract } = require('fabric-contract-api');

class IoTHashContract extends Contract {

    // ============================================
    // 1. BASIC FUNCTIONS
    // ============================================

    async storeHash(ctx, sensorID, hashValue) {
        // Use deterministic timestamp from transaction
        const txTimestamp = ctx.stub.getTxTimestamp();
        const timestamp = new Date(txTimestamp.seconds.low * 1000).toISOString();
        
        const record = {
            sensorID,
            hashValue,
            timestamp: timestamp,
            transactionID: ctx.stub.getTxID()
        };
        await ctx.stub.putState(sensorID, Buffer.from(JSON.stringify(record)));
        return JSON.stringify(record);
    }

    async queryHash(ctx, sensorID) {
        const recordBytes = await ctx.stub.getState(sensorID);
        if (!recordBytes || recordBytes.length === 0) {
            throw new Error(`Sensor ${sensorID} does not exist`);
        }
        return recordBytes.toString();
    }

    // ============================================
    // 2. BATCH OPERATIONS
    // ============================================

    async storeBatchHash(ctx, batchID, sensorIDsJson, hashValuesJson) {
        const sensorIDs = JSON.parse(sensorIDsJson);
        const hashValues = JSON.parse(hashValuesJson);

        if (sensorIDs.length !== hashValues.length) {
            throw new Error('Sensor IDs and hash values count must match');
        }
        if (sensorIDs.length === 0) {
            throw new Error('Batch cannot be empty');
        }

        // Deterministic timestamp
        const txTimestamp = ctx.stub.getTxTimestamp();
        const timestamp = new Date(txTimestamp.seconds.low * 1000).toISOString();

        const batchRecord = {
            batchID,
            sensors: [],
            timestamp: timestamp,
            transactionID: ctx.stub.getTxID(),
            count: sensorIDs.length
        };

        for (let i = 0; i < sensorIDs.length; i++) {
            batchRecord.sensors.push({
                sensorID: sensorIDs[i],
                hashValue: hashValues[i]
            });
        }

        batchRecord.merkleRoot = this.computeMerkleRoot(hashValues);
        batchRecord.batchHash = this.computeSimpleHash(batchRecord.merkleRoot + batchID);

        await ctx.stub.putState(batchID, Buffer.from(JSON.stringify(batchRecord)));

        for (const sensor of batchRecord.sensors) {
            const pointer = {
                batchID: batchID,
                sensorID: sensor.sensorID,
                storedInBatch: true
            };
            await ctx.stub.putState('BATCHREF~' + sensor.sensorID, Buffer.from(JSON.stringify(pointer)));
        }

        return JSON.stringify(batchRecord);
    }

    async queryBatch(ctx, batchID) {
        const recordBytes = await ctx.stub.getState(batchID);
        if (!recordBytes || recordBytes.length === 0) {
            throw new Error(`Batch ${batchID} does not exist`);
        }
        return recordBytes.toString();
    }

    async queryMultiple(ctx, sensorIDsJson) {
        const sensorIDs = JSON.parse(sensorIDsJson);
        const results = [];

        for (const sensorID of sensorIDs) {
            let recordBytes = await ctx.stub.getState(sensorID);
            
            if (!recordBytes || recordBytes.length === 0) {
                const batchRefBytes = await ctx.stub.getState('BATCHREF~' + sensorID);
                if (batchRefBytes && batchRefBytes.length > 0) {
                    const batchRef = JSON.parse(batchRefBytes.toString());
                    const batchBytes = await ctx.stub.getState(batchRef.batchID);
                    if (batchBytes && batchBytes.length > 0) {
                        const batch = JSON.parse(batchBytes.toString());
                        const sensorInBatch = batch.sensors.find(s => s.sensorID === sensorID);
                        if (sensorInBatch) {
                            results.push({
                                sensorID: sensorID,
                                hashValue: sensorInBatch.hashValue,
                                timestamp: batch.timestamp,
                                batchID: batchRef.batchID,
                                storedInBatch: true
                            });
                            continue;
                        }
                    }
                }
                results.push({ sensorID: sensorID, error: "Not found" });
            } else {
                results.push(JSON.parse(recordBytes.toString()));
            }
        }

        return JSON.stringify(results);
    }

    // ============================================
    // 3. HISTORY / AUDIT TRAIL
    // ============================================

    async storeHashWithHistory(ctx, sensorID, hashValue) {
        // Deterministic timestamp from transaction
        const txTimestamp = ctx.stub.getTxTimestamp();
        const timestamp = new Date(txTimestamp.seconds.low * 1000).toISOString();
        const txID = ctx.stub.getTxID();

        const historyKey = ctx.stub.createCompositeKey('HISTORY', [sensorID, timestamp, txID]);

        const record = {
            sensorID,
            hashValue,
            timestamp: timestamp,
            transactionID: txID,
            creator: ctx.clientIdentity.getID(),
            creatorOrg: ctx.clientIdentity.getMSPID()
        };

        await ctx.stub.putState(historyKey, Buffer.from(JSON.stringify(record)));

        const latestPointer = {
            latestKey: historyKey,
            timestamp: timestamp,
            transactionID: txID,
            version: await this.getNextVersion(ctx, sensorID)
        };
        await ctx.stub.putState('LATEST~' + sensorID, Buffer.from(JSON.stringify(latestPointer)));

        return JSON.stringify(record);
    }

    async queryHashLatest(ctx, sensorID) {
        const latestBytes = await ctx.stub.getState('LATEST~' + sensorID);
        if (!latestBytes || latestBytes.length === 0) {
            throw new Error(`No history found for sensor ${sensorID}`);
        }

        const latest = JSON.parse(latestBytes.toString());
        const recordBytes = await ctx.stub.getState(latest.latestKey);
        
        if (!recordBytes || recordBytes.length === 0) {
            throw new Error(`History record not found for key: ${latest.latestKey}`);
        }

        const result = JSON.parse(recordBytes.toString());
        result.version = latest.version;
        return JSON.stringify(result);
    }

    async getHistory(ctx, sensorID) {
        const iterator = await ctx.stub.getStateByPartialCompositeKey('HISTORY', [sensorID]);
        
        const results = [];
        let result = await iterator.next();
        
        while (!result.done) {
            const strValue = Buffer.from(result.value.value).toString('utf8');
            const record = JSON.parse(strValue);
            record.historyKey = result.value.key;
            results.push(record);
            result = await iterator.next();
        }
        
        await iterator.close();

        results.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        results.forEach((r, index) => { r.version = index + 1; });

        return JSON.stringify({
            sensorID: sensorID,
            totalRecords: results.length,
            history: results
        });
    }

    async verifyIntegrity(ctx, sensorID, hashToVerify) {
        const historyJson = await this.getHistory(ctx, sensorID);
        const history = JSON.parse(historyJson);
        
        const matchingRecord = history.history.find(r => r.hashValue === hashToVerify);
        
        if (matchingRecord) {
            return JSON.stringify({
                sensorID: sensorID,
                verified: true,
                matchFoundAt: matchingRecord.timestamp,
                version: matchingRecord.version,
                transactionID: matchingRecord.transactionID,
                message: "Hash verified against blockchain history"
            });
        } else {
            return JSON.stringify({
                sensorID: sensorID,
                verified: false,
                message: "Hash does not match any historical record",
                totalHistoryRecords: history.totalRecords
            });
        }
    }

    // ============================================
    // 4. ACCESS CONTROL / MULTI-ORG
    // ============================================

    async storeHashPrivate(ctx, sensorID, hashValue, allowedOrgsJson) {
        const clientMSPID = ctx.clientIdentity.getMSPID();
        const allowedOrgs = JSON.parse(allowedOrgsJson);

        if (!allowedOrgs.includes(clientMSPID)) {
            throw new Error(`Caller ${clientMSPID} not in allowed organizations list`);
        }

        // Deterministic timestamp
        const txTimestamp = ctx.stub.getTxTimestamp();
        const timestamp = new Date(txTimestamp.seconds.low * 1000).toISOString();

        const record = {
            sensorID,
            hashValue,
            ownerOrg: clientMSPID,
            allowedOrgs: allowedOrgs,
            timestamp: timestamp,
            transactionID: ctx.stub.getTxID(),
            privateData: true
        };

        await ctx.stub.putState('PRIVATE~' + sensorID, Buffer.from(JSON.stringify(record)));
        return JSON.stringify(record);
    }

    async queryHashPrivate(ctx, sensorID) {
        const clientMSPID = ctx.clientIdentity.getMSPID();
        const privateKey = 'PRIVATE~' + sensorID;
        
        const recordBytes = await ctx.stub.getState(privateKey);
        if (!recordBytes || recordBytes.length === 0) {
            throw new Error(`Private record for sensor ${sensorID} does not exist`);
        }

        const record = JSON.parse(recordBytes.toString());

        const isOwner = record.ownerOrg === clientMSPID;
        const isAllowed = record.allowedOrgs.includes(clientMSPID);

        if (!isOwner && !isAllowed) {
            throw new Error(`Access denied: ${clientMSPID} is not authorized. Owner: ${record.ownerOrg}`);
        }

        record.accessedBy = clientMSPID;
        record.accessType = isOwner ? 'OWNER' : 'AUTHORIZED';

        return JSON.stringify(record);
    }

    async transferOwnership(ctx, sensorID, newOwnerOrg) {
        const clientMSPID = ctx.clientIdentity.getMSPID();
        const privateKey = 'PRIVATE~' + sensorID;
        
        const recordBytes = await ctx.stub.getState(privateKey);
        if (!recordBytes || recordBytes.length === 0) {
            throw new Error(`Private record for sensor ${sensorID} does not exist`);
        }

        const record = JSON.parse(recordBytes.toString());

        if (record.ownerOrg !== clientMSPID) {
            throw new Error(`Only owner (${record.ownerOrg}) can transfer ownership`);
        }

        const previousOwner = record.ownerOrg;
        record.ownerOrg = newOwnerOrg;
        
        if (!record.allowedOrgs.includes(previousOwner)) {
            record.allowedOrgs.push(previousOwner);
        }
        if (!record.allowedOrgs.includes(newOwnerOrg)) {
            record.allowedOrgs.push(newOwnerOrg);
        }

        record.transferHistory = record.transferHistory || [];
        
        // Deterministic timestamp
        const txTimestamp = ctx.stub.getTxTimestamp();
        const timestamp = new Date(txTimestamp.seconds.low * 1000).toISOString();
        
        record.transferHistory.push({
            from: previousOwner,
            to: newOwnerOrg,
            timestamp: timestamp,
            transactionID: ctx.stub.getTxID()
        });

        await ctx.stub.putState(privateKey, Buffer.from(JSON.stringify(record)));
        
        return JSON.stringify({
            sensorID: sensorID,
            previousOwner: previousOwner,
            newOwner: newOwnerOrg,
            message: "Ownership transferred successfully"
        });
    }

    // ============================================
    // 5. UTILITY FUNCTIONS
    // ============================================

    async getAllSensors(ctx, startKey, endKey, pageSize) {
        const size = parseInt(pageSize) || 10;
        const start = startKey || 'sensor0';
        const end = endKey || 'sensorzzzzzz';
        
        const iterator = await ctx.stub.getStateByRange(start, end);
        
        const results = [];
        let count = 0;
        let result = await iterator.next();
        
        while (!result.done && count < size) {
            const strValue = Buffer.from(result.value.value).toString('utf8');
            try {
                const record = JSON.parse(strValue);
                if (record.sensorID && result.value.key.indexOf('~') === -1) {
                    results.push({
                        key: result.value.key,
                        record: record
                    });
                    count++;
                }
            } catch (e) {
                // Skip non-JSON entries
            }
            result = await iterator.next();
        }
        
        await iterator.close();
        
        return JSON.stringify({
            totalReturned: results.length,
            startKey: start,
            records: results
        });
    }

    async deleteSensor(ctx, sensorID) {
        await ctx.stub.deleteState(sensorID);
        return JSON.stringify({
            sensorID: sensorID,
            deleted: true,
            message: "Sensor deleted successfully"
        });
    }

    // ============================================
    // 6. HELPER METHODS
    // ============================================

    computeSimpleHash(input) {
        let hash = 0;
        for (let i = 0; i < input.length; i++) {
            const char = input.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(16).padStart(8, '0');
    }

    computeMerkleRoot(hashes) {
        if (hashes.length === 0) return '';
        if (hashes.length === 1) return hashes[0];

        let level = [...hashes].sort();
        
        while (level.length > 1) {
            const nextLevel = [];
            for (let i = 0; i < level.length; i += 2) {
                if (i + 1 < level.length) {
                    nextLevel.push(this.computeSimpleHash(level[i] + level[i + 1]));
                } else {
                    nextLevel.push(level[i]);
                }
            }
            level = nextLevel;
        }
        
        return level[0];
    }

    async getNextVersion(ctx, sensorID) {
        const latestBytes = await ctx.stub.getState('LATEST~' + sensorID);
        if (!latestBytes || latestBytes.length === 0) {
            return 1;
        }
        const latest = JSON.parse(latestBytes.toString());
        return (latest.version || 1) + 1;
    }

    async init(ctx) {
        console.log('IoTHashContract initialized');
        return JSON.stringify({
            status: 'initialized',
            contract: 'IoTHashContract',
            version: '2.0.1',
            features: ['basic', 'batch', 'history', 'access-control', 'deterministic']
        });
    }
}

module.exports.IoTHashContract = IoTHashContract;
module.exports.contracts = [IoTHashContract];