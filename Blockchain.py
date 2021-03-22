#import sys
import datetime
import json
import pathlib

import time
#=======ALGORITHM===========
#from u_quark import digest
#from d_quark import digest
#from s_quark import digest
#from c_quark import digest
import hashlib
#===========================

from ecdsa import SECP256k1, VerifyingKey, BadSignatureError
import codecs

from flask import Flask, jsonify, request
import requests


# Building Blockchain
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transaction = [] #mempools
        self.nodes_file = "nodes.json"
        self.nodes = {} #empty set
        self.url_address = "127.0.0.1:5001"
        #print(self.read_node())
        network = self.file_check()#read_node()
        print(network)
        #self.file_check()
        self.proof = 1
        self.previous_hash = '0'
        if len(network) == 1:
            print("buat block baru")
            print("Please insert a coin to the blockchain")
            print("Address = 52ae914cb8bfd8d2ee6d46cb3bb188019fbef3d21adf1550f06958889656178c74df99dbe588e03a6992c50f76226c0c9ad5d7aeec1a8c874511a82c8fd3b8c1")
            
            self.create_block(self.previous_hash)
        else:
            print("replace block baru")
            self.replace_chain()
    
    def read_node(self):
        file_read = open(self.nodes_file, "r")
        file_read.seek(0)
        data = file_read.read()
        file_read.close()

        json_file = json.loads(data)
        return json_file["nodes"]
        
    
    def tx_validation(self, input_):
        
        json_input = input_
        public_key = json_input[0]['sender_public_key']
        signature =  json_input[0]['signature']
        prev_tx = json_input[0]['previous_tx']

        vk_byte = codecs.decode(public_key, 'hex')
        vk = VerifyingKey.from_string(vk_byte, curve=SECP256k1)
        
        signature_byte = codecs.decode(signature, 'hex')
        prev_tx_byte = prev_tx.encode('utf-8')
        check_sig = vk.verify(signature_byte,prev_tx_byte)
        
        return check_sig
    
    
# =============================================================================
#     def simple_merkleTree(self, transaction):
#         hashlist = []
#         for i in transaction:
#             transaction_dump = json.dumps(i).encode()
#             transaction_hash = hashlib.sha256(transaction_dump).hexdigest()
#             hashlist.append(transaction_hash)
#         
#         return hashlib.sha256("".join(hashlist).encode()).hexdigest
# =============================================================================

    def create_block(self, previous_hash):
        if self.transaction == []: #seharusnya ini bukan self transaction tapi self chain
            
            input_address = "52ae914cb8bfd8d2ee6d46cb3bb188019fbef3d21adf1550f06958889656178c74df99dbe588e03a6992c50f76226c0c9ad5d7aeec1a8c874511a82c8fd3b8c1"
            input_tx = int(input("Input coin  = "))
            
            genesis_transaction = {
              'input' : [{'previous_tx' : 0,
                        'index' : 0 }],
    
            'output' : [{'amount' : input_tx,
                        'receiver_public_key' : input_address}]}
            dumps_hash_tx = json.dumps(genesis_transaction, default = str).encode() # for all algorithm that hashlib provide
            #dumps_hash_tx = json.dumps(genesis_transaction, default = str)for Quark Algorithm
            #hash_tx = digest(dumps_hash_tx)  for Quark Algorithm
            hash_tx = hashlib.sha256(dumps_hash_tx).hexdigest() # for all algorithm that hashlib provide
            hash_tx_dict = {'hash':hash_tx}
            genesis_transaction.update(hash_tx_dict)
            
            block = {
                    'index' : len(self.chain) + 1,
                    'timestamp' : datetime.datetime.now(),
                    'proof' : self.proof,
                    'previous_hash' : previous_hash,
                    'transaction_hash' : "0",
                    'transaction' : [genesis_transaction]}
            output = self.proof_of_work(block)
            block['proof'] = output['proof']
            block['hash'] = output['hash']
            self.transaction = []
            self.chain.append(block)
        else:
            block = {
                    'index' : len(self.chain) + 1,
                    'timestamp' : datetime.datetime.now(),
                    'proof' : self.proof,
                    'previous_hash' : previous_hash,
                    'transaction_hash' : "Not Available",#self.simple_merkleTree(self.transaction),
                    'transaction' : self.transaction}
            output = self.proof_of_work(block)
            block['proof'] = output['proof']
            block['hash'] = output['hash']
            print("output = ",output)
            self.transaction = []
            self.chain.append(block)
            network = self.read_node()
            #print("network")
            for nodes in network:
                #print("Inside network for")
                requests.get(f'http://{nodes}/replace_chain')#NYANGKUT DISNIIIIII
                #print("Replace chain")
        return block
    
    def  get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, mine_block):
        proof = 1
        check_proof = False
        output = {}
        while check_proof is False:
            mine_block['proof'] = proof
            hash_operation = self.hash(mine_block)
            if hash_operation[:1] == '0':
            #if hash_operation[:4] == '0000' :
                #hash_previous_block = hash_operation
                output['hash'] = hash_operation
                output['proof'] = proof
                #self.block['hash'] = hash_operation
                print("Hasil nonce = ",proof)#macet di sini
                print("Hasil hash=",hash_operation)#macet disnii
                check_proof = True
            else : 
                print("Nonce = ",proof)
                print("hash from ^ nonce = ",hash_operation)
                proof += 1
        return output
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True, default = str).encode()# for all algorithm that hashlib provide
        #encoded_block1 = json.dumps(block, sort_keys = True, default = str) for QUARK algorithm

        #return digest(encoded_block1) for QUARK algorithm
        return hashlib.sha256(encoded_block).hexdigest() # for all algorithm that hashlib provide
    
    def add_transaction(self, sender, receiver, hash_ ):
        self.transaction.append({'input' : sender ,
                                 'output' : receiver,
                                 'hash' : hash_})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
        
    def replace_chain(self):
        network = self.read_node()
        longest_chain = None
        max_length = len(self.chain)
        
        for nodes in network:
            if nodes == self.url_address:
                length = max_length
                chain = self.chain
            else:
                response = requests.get(f'http://{nodes}/get_chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
            if length > max_length:
                max_length = length
                longest_chain = chain
        if longest_chain: #TRUE
            print("longest chain")
            self.chain = longest_chain
            return True
        return False
                    
    def distributed_transaction(self):#distributed mempool
        network = self.read_node()
        
        for nodes in network:
            response1 = requests.get(f'http://{nodes}/check_transaction')
            #response2 = requests.get(f'http://{nodes}/get_chain')
            if response1.status_code == 200:
                transaction = response1.json()['transaction']
                #length = response2.json()['length']
                self.transaction = transaction
                return True
            
        return False
    
    def file_check(self):
        file = pathlib.Path(self.nodes_file)
        if file.exists():    
            file_read = open(self.nodes_file, "r")
            file_read.seek(0)
            data = file_read.read()
            file_read.close()

            json_file = json.loads(data)
    
            self.nodes.update(json_file) 
            print(self.nodes)
            print("File Exist")
            
            self.replace_chain()

            json_file["nodes"].append(self.url_address)

            file_write = open(self.nodes_file, "w")
            file_write.write(json.dumps(json_file))
            file_write.close()
            return json_file["nodes"]
    
        else:
            f = open(self.nodes_file, "w+")
            wallet_tx = {"nodes" : [self.url_address]}
            json_data = json.dumps(wallet_tx)
            json_file = json.loads(json_data)
            f.write(json_data)
            f.close()
            return json_file["nodes"]
            
                    
# Mining Blockchain
        
# 1. creating web app
app = Flask(__name__)        

# 2. creating blockchain
blockchain = Blockchain()

# 3. mining new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    start_time = time.time()
    previous_block = blockchain.get_previous_block()
    previous_hash = previous_block['hash']
    block = blockchain.create_block(previous_hash)
    end_time = time.time()
    processing_time = end_time - start_time
    
    response = {
                'messages' : 'Congratulation you just mined a block',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transaction' : block['transaction'],
                'hashing_time' : processing_time
                }
    return jsonify(response), 200

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {
                'chain' : blockchain.chain, 
                'length' : len(blockchain.chain)
                }
    return jsonify(response), 200


# adding transcation to mempool
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['input', 'output', 'hash']
    if not all(key in json for key in transaction_keys):
        return 'Lengkapi data yang dibutuhkan', 400
    try:
        blockchain.tx_validation(json['input'])
        index = blockchain.add_transaction(json['input'], json['output'], json['hash'])
        response = {'messages' : f'transaction akan dimasukkan ke dalam block ke {index}'}
        return jsonify(response), 201
    except BadSignatureError:
        response = {'messages' : 'Transaksi di gagalkan'}
        return jsonify(response), 403
    

# decentralising blockhain
@app.route('/connect_node', methods = ['POST']) #akan dihapus
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No Node', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'messages' : 'All the node are connected', 
                'total_nodes' : list(blockchain.nodes) 
                    }
    return jsonify(response), 201

@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    print("replace chain API")
    replace_chain = blockchain.replace_chain()
    print("after replace chain")
    blockchain.transaction = []
    if replace_chain: # TRUE
        response = {'messages' : 'Chain replaced',
                    'new chain' : blockchain.chain}
    else: # FALSE
        response = {'messages' : 'Chain not replaced',
                    'chain' : blockchain.chain}
    return jsonify(response), 200

@app.route('/distributed_mempool', methods = ['GET'])
def distributed_mempool():
    distributed_mempool = blockchain.distributed_transaction()
    if distributed_mempool: # TRUE
        response = {'messages' : 'Mempool updated',
                    'new chain' : blockchain.transaction}
    else: # FALSE
        response = {'messages' : 'Mempool not updated',
                    'chain' : blockchain.transaction}
    return jsonify(response), 200

@app.route('/check_nodes', methods = ['GET'])
def check_nodes():
    checking = blockchain.read_node()
    #response = {'nodes' : checking}
    return jsonify(checking), 200

@app.route('/check_transaction', methods = ['GET'])
def check_transaction():
    check_mempool = blockchain.transaction
    response = {'transaction' : check_mempool}
    return jsonify(response), 200


@app.route('/quit_network', methods = ['GET'])
def quit_network():
    #print("hallo lagi")
    file_read = open(blockchain.nodes_file, "r")
    file_read.seek(0)
    data = file_read.read()
    file_read.close()
    json_file = json.loads(data)
    json_file["nodes"].remove(blockchain.url_address)
    blockchain.nodes.update(json_file)
    file_write = open(blockchain.nodes_file, "w")
    file_write.write(json.dumps(json_file))
    file_write.close()
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if shutdown:
        shutdown()
    response = {'message' : "Telah berpisah dari Network"}
    return response

app.run(host = '0.0.0.0', port = 5001)