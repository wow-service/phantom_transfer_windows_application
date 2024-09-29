from PySide6.QtCore import QThread, Signal
from solana.rpc.api import Keypair, Pubkey
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
from solana.rpc.core import RPCException
from solana.exceptions import SolanaRpcException


class NetworkRequestThread(QThread):
    finished = Signal(str)

    def __init__(self, cli, transaction_list):
        super().__init__()
        self.transaction_list = transaction_list
        self.cli = cli

    def func_transfer_sol(self, bs58_keypair_string, receiver_address, send_lamport):
        sender = Keypair.from_base58_string(bs58_keypair_string)
        transfer_ix = transfer(TransferParams(from_pubkey=sender.pubkey(),
                                              to_pubkey=Pubkey.from_string(receiver_address),
                                              lamports=int(float(send_lamport) * 1e9)))
        txn = Transaction().add(transfer_ix)
        try:
            hash_tx = self.cli.send_transaction(txn, sender).value
            return f'[Success] - Transaction hash: {hash_tx}'
        except RPCException as e:
            return f'[Failed] - Sender: {sender.pubkey()}, Error info: {e.args[0].message}'
        except SolanaRpcException:
            return f'[Failed] - Network connection failed'

    def run(self):
        for transfer_data in self.transaction_list:
            results_text = self.func_transfer_sol(transfer_data[0], transfer_data[1][0], transfer_data[1][1])
            self.finished.emit(results_text)
