import hashlib
import json
import time
from typing import List

class MultiSigWallet:
    """Ví MultiSig để quản lý chữ ký giao dịch, mining, và hợp đồng thông minh."""
    def __init__(self, owners: List[str], required_sigs: int):
        self.owners = set(owners)
        self.required_sigs = required_sigs

    def validate_signatures(self, signatures: List[str]) -> bool:
        """Kiểm tra xem chữ ký có hợp lệ không."""
        unique_sigs = set(signatures)
        return len(unique_sigs & self.owners) >= self.required_sigs

class Block:
    """Block trong blockchain"""
    def __init__(self, index, previous_hash, transactions, miner_signatures, timestamp=None):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.miner_signatures = miner_signatures
        self.timestamp = timestamp or time.time()
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Tạo hash của block"""
        block_string = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": self.transactions,
            "miner_signatures": self.miner_signatures,
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        """Đào block với độ khó nhất định"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

class Blockchain:
    """Blockchain hỗ trợ MultiSig"""
    def __init__(self, difficulty=2):
        self.chain = [self.create_genesis_block()]
        self.difficulty = difficulty
        self.pending_transactions = []
        self.miner_wallet = MultiSigWallet(["miner1", "miner2", "miner3"], 2)  # Cần ít nhất 2 chữ ký để đào block
        self.smart_contracts = {}  # Lưu danh sách smart contract

    def create_genesis_block(self):
        """Tạo block gốc"""
        return Block(0, "0", [], [], time.time())

    def add_transaction(self, sender, receiver, amount, signatures):
        """Thêm giao dịch nếu đủ chữ ký"""
        wallet = MultiSigWallet([sender, receiver], 2)  # Ví dụ: Cần chữ ký từ cả sender và receiver
        if wallet.validate_signatures(signatures):
            self.pending_transactions.append({
                "sender": sender,
                "receiver": receiver,
                "amount": amount,
                "signatures": signatures
            })
            return True
        return False

    def mine_pending_transactions(self, miner_signatures):
        """Đào block mới nếu miner có đủ chữ ký"""
        if self.miner_wallet.validate_signatures(miner_signatures):
            new_block = Block(len(self.chain), self.chain[-1].hash, self.pending_transactions, miner_signatures)
            new_block.mine_block(self.difficulty)
            self.chain.append(new_block)
            self.pending_transactions = []
            return True
        return False

    def deploy_contract(self, contract_name, owners, required_sigs):
        """Triển khai một smart contract MultiSig"""
        self.smart_contracts[contract_name] = MultiSigWallet(owners, required_sigs)

    def execute_contract(self, contract_name, signatures):
        """Thực thi smart contract nếu đủ chữ ký"""
        if contract_name in self.smart_contracts:
            contract_wallet = self.smart_contracts[contract_name]
            return contract_wallet.validate_signatures(signatures)
        return False

    def get_chain(self):
        """Trả về danh sách các block"""
        return [block.__dict__ for block in self.chain]
