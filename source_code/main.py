import json
import sys

from solana.rpc.api import Keypair, Client, Pubkey
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
from solana.rpc.core import RPCException

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QFrame, QHBoxLayout, QComboBox, \
    QPushButton, QTableWidget, QCheckBox, QTableWidgetItem, QTextBrowser


from utils import NetworkRequestThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        networks = self.load_network_data()
        self.thread = None
        self.init_thread = None
        self.network_mapping = {
            'mainnet': networks.get('mainnet'),
            'testnet': networks.get('testnet'),
            'devnet': networks.get('devnet')
        }
        self.endpoint = self.network_mapping.get('mainnet')
        self.cli = Client(self.endpoint)
        self.setWindowTitle("Solana Wallet Windows Application")
        self.resize(1400, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_layout = QVBoxLayout(central_widget)
        right_layout = QVBoxLayout(central_widget)

        self.comboBox = QComboBox()
        self.comboBox.setFixedHeight(30)
        self.comboBox.addItem("MainnetBeta")
        self.comboBox.addItem("Testnet")
        self.comboBox.addItem("Devnet")

        self.comboBox.currentIndexChanged.connect(self.on_combobox_changed)

        self.table = QTableWidget()
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setStyleSheet("background-color: lightblue;")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Status', 'Sender Address', 'Balance'])
        self.senders_secrets, self.senders_list = self.load_senders_data()
        self.table.setRowCount(len(self.senders_list))
        self.table.setFixedWidth(700)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 400)
        self.table.setColumnWidth(2, 200)

        # 将多选按钮添加到表格中

        for i, sender_value in enumerate(self.senders_list):
            checkbox = QCheckBox()
            self.table.setCellWidget(i, 0, checkbox)
            self.table.setItem(i, 1, QTableWidgetItem(sender_value.get('address')))
            self.table.setItem(i, 2, QTableWidgetItem(str(sender_value.get('balance'))))

        self.table1 = QTableWidget()
        self.table1.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table1.setStyleSheet("background-color: lightgreen;")
        self.table1.setColumnCount(3)
        self.table1.setHorizontalHeaderLabels(['Status', 'Receiver Address', 'Send Amount'])

        receivers_list = self.load_receivers_data()
        self.table1.setRowCount(len(receivers_list))
        self.table1.setFixedWidth(700)
        self.table1.setColumnWidth(0, 50)
        self.table1.setColumnWidth(1, 400)
        self.table1.setColumnWidth(2, 200)

        # 将多选按钮添加到表格中
        for i, receiver_item in enumerate(receivers_list):
            checkbox = QCheckBox()
            # checkbox.stateChanged.connect(self.receivers_on_checkbox_state_changed)
            self.table1.setCellWidget(i, 0, checkbox)
            self.table1.setItem(i, 1, QTableWidgetItem(receiver_item.get('address')))
            self.table1.setItem(i, 2, QTableWidgetItem(str(receiver_item.get('balance'))))

        # 发送按钮
        self.send_btn = QPushButton("Send", self)
        self.send_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #AB9FF2;
                        border-style: outset;
                        border-width: 2px;
                        border-radius: 10px;
                        border-color: beige;
                        font: bold 14px;
                        min-width: 10em;
                        padding: 6px;
                    }
                    QPushButton:hover {
                        background-color: red;
                        border-style: inset;
                    }
                """)
        self.send_btn.clicked.connect(self.on_transfer_sol)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #AB9FF2;
                                border-style: outset;
                                border-width: 2px;
                                border-radius: 10px;
                                border-color: beige;
                                font: bold 14px;
                                min-width: 10em;
                                padding: 6px;
                            }
                            QPushButton:hover {
                                background-color: red;
                                border-style: inset;
                            }
                        """)

        # 创建一个水平分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)

        v_line = QFrame()
        v_line.setFrameShape(QFrame.Shape.VLine)
        v_line.setFrameShadow(QFrame.Shadow.Sunken)

        # 将部件和分隔线添加到布局中
        left_layout.addWidget(self.comboBox)
        left_layout.addWidget(self.table)
        left_layout.addWidget(line)
        left_layout.addWidget(self.table1)
        left_layout.addWidget(self.send_btn)
        self.log_browser = QTextBrowser(self)
        self.log_browser.setStyleSheet("background-color: #293134; color: white;")
        right_layout.addWidget(self.log_browser)

        right_layout.addWidget(self.clear_btn)
        self.clear_btn.clicked.connect(self.clear_log_text)
        main_layout.addLayout(left_layout)
        main_layout.addWidget(v_line)
        main_layout.addLayout(right_layout)
        self.center()

    def load_senders_data(self):
        with open('db/senders.json') as f:
            senders = json.load(f)

        senders_pubkey = [Keypair.from_base58_string(sender).pubkey() for sender in senders]

        accounts_value = self.cli.get_multiple_accounts(senders_pubkey).value
        senders_account = [
            {'address': senders_pubkey[i].__str__(),
             'balance': accounts_value[i].lamports / 1e9 if accounts_value[i] else 0}
            for i in range(len(senders_pubkey))]
        return senders, senders_account

    @staticmethod
    def load_network_data():
        with open('db/endpoints.json') as f:
            _networks = json.load(f)
        return _networks

    @staticmethod
    def load_receivers_data():
        with open('db/receivers.json') as f:
            receivers = json.load(f)

        receivers_account = [
            {'address': receivers[i].__str__(), 'balance': "0.1"}
            for i in range(len(receivers))]
        return receivers_account

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

    def clear_log_text(self):
        self.log_browser.clear()

    def on_transfer_sol(self):
        self.update_logger_text('[Tips] - The transaction has been submitted, please wait ...')

        senders_selected_data = []
        receivers_selected_data = []

        for i in range(self.table.rowCount()):
            check_box_status = self.table.cellWidget(i, 0)
            if check_box_status.isChecked():
                senders_selected_data.append(self.senders_secrets[i])

        for i in range(self.table1.rowCount()):
            check_box_status = self.table1.cellWidget(i, 0)
            if check_box_status.isChecked():
                address = self.table1.item(i, 1)
                value = self.table1.item(i, 2)
                receivers_selected_data.append((address.text(), value.text()))
        transaction_list = [(sender, receiver) for receiver in receivers_selected_data for sender in
                            senders_selected_data]
        self.thread = NetworkRequestThread(self.cli, transaction_list)
        self.thread.finished.connect(self.update_logger_text)
        self.thread.start()

    def update_logger_text(self, message):
        log_message = f"{message}"
        self.log_browser.append(log_message)

    def center(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_size = self.size()
        x = (screen_geometry.width() - window_size.width()) // 2
        y = (screen_geometry.height() - window_size.height()) // 2
        self.move(x, y)

    def on_combobox_changed(self, index):
        if index == 0:
            self.endpoint = self.network_mapping.get('mainnet')
            self.cli = Client(self.endpoint)
        elif index == 1:
            self.endpoint = self.network_mapping.get('testnet')
            self.cli = Client(self.endpoint)
        else:
            self.endpoint = self.network_mapping.get('devnet')
            self.cli = Client(self.endpoint)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
