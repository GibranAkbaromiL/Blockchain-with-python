from ecdsa import SigningKey, SECP256k1
import codecs
import hashlib
import json
import pathlib
import requests


class Wallet:
    def __init__(self):
        self.private_key = "60cf347dbc59d31c1358c8e5cf5e45b822ab85b79cb32a9f3d98184779a9efc1"
        
        byte_ = codecs.decode(self.private_key, 'hex')
        self.sk = SigningKey.from_string(byte_, curve=SECP256k1)
        vk = self.sk.verifying_key #public key
        self.vk_toString = vk.to_string().hex()

        ripemd160 = hashlib.new('ripemd160') #calling ripemd160
        ripemd160.update(self.vk_toString.encode())
        self.encrypted_public_key = ripemd160.hexdigest() #encrypted public key
        self.previous_tx = "0"
        self.filename = "wallet.json"
        self.nodes_file = "nodes.json"
        self.file_check()

    def new(self, private_key, public_key, address):
        
        f = open(self.filename, "w+")
        wallet_tx = {"private_key" : private_key,
                     "public_key" : public_key,
                     "address" : address,
                     "transaction" : []}
        f.write(json.dumps(wallet_tx))
        f.close()
        
    
    def broadcast(self, transaction):
        file_read = open(self.nodes_file, "r")
        file_read.seek(0)
        data = file_read.read()
        file_read.close()

        json_file = json.loads(data)
        
        for nodes in json_file['nodes']:
            url = f"http://{nodes}/add_transaction"
            response = requests.post(url, json=transaction).json()
            print(f"{nodes, response}")
        
        return print("broadcast to mempool")
    
    def transaction(self, yang_dimiliki):
        input_address = input("masukkan address = ")
        amount = int(input("masukkan jumlah = "))
        #print(self.failed_signature)
        
        public_key = self.vk_toString
        previous_tx = self.previous_tx
        byte_prev = previous_tx.encode()
        byte_signature = self.sk.sign(byte_prev)
        signature = byte_signature.hex()
        
        if yang_dimiliki > amount:
            kembalian = yang_dimiliki - amount            

            tx = {
                  'input' : [{'previous_tx' : previous_tx,
                            'index' : 0, #nilai index ke berapa yang di ambil dr output transaksi sebelumnya
                            'signature' : signature, #signature dari private key dengan hash tx sebelumnya
                            'sender_public_key' : public_key ,
                            'amount':yang_dimiliki}],
        
                'output' : [{'amount' : amount,
                            'receiver_public_key' : input_address},
                            {'amount' : kembalian,
                            'receiver_public_key' : public_key}]} #reciever publik key is hash
    
            dumps_hash_tx = json.dumps(tx, default = str).encode()
    
            hash_tx = hashlib.sha256(dumps_hash_tx).hexdigest()
            
            #dumps_hash_tx = json.dumps(tx, default = str)
    
            #hash_tx = digest(dumps_hash_tx)
            
            hash_tx_dict = {"hash" : hash_tx}
            
            tx.update(hash_tx_dict)
            return tx
        else:
            print("Please insert the correct amount")
            self.transaction()
    
    def get_transaction(self):
        file_read = open(self.nodes_file, "r")
        file_read.seek(0)
        data = file_read.read()
        file_read.close()

        json_file = json.loads(data)
        public_key = self.vk_toString
        
        for nodes in json_file['nodes']:
            url = f"http://{nodes}/get_chain"
            response = requests.get(url)
            response_status_code = response.status_code
            response_json = response.json()
            length_block = response_json['length'] -1
            if response_status_code == 200:
                #print(response_status_code)
                transaction = response_json['chain'][length_block]['transaction']
                #print(response_json['chain'][length_block]['transaction'])
                for x in transaction:
                    #print(type(x))
                    for y in x['output']:
                        if y['receiver_public_key'] == public_key:
                            print("you have = ",y['amount'])
                            #print(type(y['amount']))
                            return y['amount']
                        else:
                            print("sorry you dont have any coins yet")
                            return 0
    
    
    def file_check(self):
        private_key = self.private_key
        public_key = self.vk_toString
        address = self.encrypted_public_key
        file = pathlib.Path(self.filename)
        if file.exists():    
            print("PUBLIC KEY = ", public_key)
            get_tx = self.get_transaction()
            if get_tx > 0:
                print("POST TRANSACTION")
                file_read = open(self.filename, "r")
                file_read.seek(0)
                data = file_read.read()
                file_read.close()
    
                jsonfile = json.loads(data)
            
                tx = self.transaction(get_tx)

                json_tx = jsonfile["transaction"].append(tx)

                json_data = json.dumps(jsonfile["transaction"])
                file_write = open(self.filename, "w")
                file_write.write(json.dumps(jsonfile))
                file_write.close()

                self.broadcast(tx)
        else:
            self.new(private_key=private_key, public_key=public_key, address=address)
            print("make new file")
            self.file_check()

wallet = Wallet()







