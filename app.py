import streamlit as st
import hashlib
import time
import json

# --- Lớp Block để lưu trữ giao dịch trong Blockchain ---
class Block:
    def __init__(self, index, transactions, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{json.dumps(self.transactions)}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty=2):
        while self.hash[:difficulty] != "0" * difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()

# --- Lớp Blockchain ---
class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, "Genesis Block", "0")

    def add_block(self, transactions):
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), transactions, previous_block.hash)
        new_block.mine_block()
        self.chain.append(new_block)

# --- Khởi tạo Session State ---
if "users" not in st.session_state:
    st.session_state["users"] = {}

if "multisig_wallets" not in st.session_state:
    st.session_state["multisig_wallets"] = {}

if "blockchain" not in st.session_state:
    st.session_state["blockchain"] = Blockchain()

# --- Đăng ký / Đăng nhập ---
st.header("🔐 Đăng nhập hoặc Đăng ký")

username = st.text_input("Nhập tên tài khoản")
if st.button("Đăng ký"):
    if username not in st.session_state["users"]:
        st.session_state["users"][username] = {"wallets": []}
        st.success("✅ Đăng ký thành công!")
    else:
        st.warning("⚠ Tài khoản đã tồn tại!")

if st.button("Đăng nhập"):
    if username in st.session_state["users"]:
        st.session_state["current_user"] = username
        st.success(f"✅ Đăng nhập thành công! Xin chào **{username}**")
    else:
        st.error("❌ Tài khoản không tồn tại! Vui lòng đăng ký trước.")

current_user = st.session_state.get("current_user", None)

# --- Chọn hoặc tạo Ví MultiSig ---
st.header("🏦 Quản lý Ví MultiSig")

wallet_name = st.text_input("Nhập tên ví MultiSig mới")
if st.button("Tạo Ví MultiSig"):
    if wallet_name and wallet_name not in st.session_state["multisig_wallets"]:
        st.session_state["multisig_wallets"][wallet_name] = {
            "owners": [current_user],  # Người tạo là owner
            "transactions": [],
            "threshold": 2
        }
        st.session_state["users"][current_user]["wallets"].append(wallet_name)
        st.success(f"✅ Ví '{wallet_name}' đã được tạo!")
    else:
        st.warning("⚠ Tên ví đã tồn tại hoặc không hợp lệ!")

# Hiển thị các ví mà user có quyền truy cập
if current_user:
    if "wallets" not in st.session_state["users"][current_user]:
        if "users" not in st.session_state or not isinstance(st.session_state["users"], dict):
            st.session_state["users"] = {}

        if current_user:
            if current_user not in st.session_state["users"] or not isinstance(st.session_state["users"][current_user], dict):
                st.session_state["users"][current_user] = {"wallets": []}

    user_wallets = st.session_state["users"][current_user]["wallets"]
    selected_wallet = st.selectbox("Chọn Ví MultiSig", user_wallets if user_wallets else ["Chưa có ví"])

    if selected_wallet != "Chưa có ví":
        wallet = st.session_state["multisig_wallets"][selected_wallet]

        # --- Quản lý Chủ sở hữu ---
        st.subheader(f"👥 Chủ sở hữu Ví '{selected_wallet}'")

        new_owner = st.text_input("Thêm địa chỉ đồng ký (tài khoản đã đăng ký)")
        if st.button("Thêm Chủ sở hữu"):
            if new_owner in st.session_state["users"]:
                if new_owner not in wallet["owners"]:
                    wallet["owners"].append(new_owner)
                    if new_owner in st.session_state["users"]:
                        if not isinstance(st.session_state["users"][new_owner], dict):
                            st.session_state["users"][new_owner] = {"wallets": []}  # Reset về dictionary hợp lệ
                    else:
                        st.session_state["users"][new_owner] = {"wallets": []}  # Tạo mới nếu chưa tồn tại

                    st.session_state["users"][new_owner]["wallets"].append(selected_wallet)
                    st.success(f"✅ Đã thêm {new_owner} vào Ví '{selected_wallet}'")
                else:
                    st.warning("⚠ Người này đã là đồng ký!")
            else:
                st.error("❌ Tài khoản không tồn tại!")

        st.write(f"🔑 **Chủ sở hữu hiện tại:** {wallet['owners']}")
        max_signatures = max(1, len(wallet["owners"]))  # Đảm bảo min_value không lớn hơn max_value
        threshold = st.number_input("📌 Số chữ ký cần thiết để xác nhận giao dịch",
                                    min_value=1, 
                                    max_value=max_signatures,
                                    value=min(wallet["threshold"], max_signatures))
        if st.button("Cập nhật ngưỡng chữ ký"):
            wallet["threshold"] = threshold
            st.success(f"✅ Ngưỡng chữ ký đã cập nhật ({wallet['threshold']})")

        # --- Tạo Giao Dịch ---
        st.subheader("💰 Tạo Giao Dịch")

        receiver = st.text_input("Nhập địa chỉ ví người nhận")
        amount = st.number_input("Nhập số tiền", min_value=0.01, format="%.2f")

        if st.button("Tạo Giao Dịch"):
            txn = {"sender": current_user, "receiver": receiver, "amount": amount, "signatures": []}
            wallet["transactions"].append(txn)
            st.success("✅ Giao dịch đã được tạo!")

        # --- Ký Giao Dịch ---
        st.subheader("✍️ Ký Giao Dịch")

        if isinstance(wallet["transactions"], list):
            for i, txn in enumerate(wallet["transactions"]):
                if isinstance(txn, str):  
                    txn = json.loads(txn)  # Chuyển chuỗi JSON thành dictionary

                if isinstance(txn, dict):  
                    st.write(f"🔹 **Giao dịch #{i}:** {txn}")
                    if current_user in wallet["owners"]:
                        if st.button(f"Ký giao dịch #{i}", key=f"sign_{i}"):
                            if current_user not in txn["signatures"]:
                                txn["signatures"].append(current_user)
                                wallet["transactions"][i] = txn  # Cập nhật lại danh sách
                                st.success(f"✅ {current_user} đã ký giao dịch #{i}")
                            else:
                                st.warning("⚠ Bạn đã ký giao dịch này rồi!")

        # --- Mining Block ---
        st.subheader("⛏️ Mining Block")

        if len(wallet["transactions"]) > 0:
            txn_index = st.selectbox("Chọn giao dịch để mining", range(len(wallet["transactions"])), key="txn_mining")
            txn = wallet["transactions"][txn_index]

            if len(txn["signatures"]) >= wallet["threshold"]:
                if st.button("Mine Block"):
                    st.session_state["blockchain"].add_block([txn])
                    wallet["transactions"].pop(txn_index)
                    st.success("✅ Giao dịch đã được lưu vào blockchain!")
            else:
                st.warning("⚠ Chưa đủ chữ ký để mining!")

        # --- Hiển thị Blockchain ---
        st.subheader("📜 Chuỗi Blockchain")

        for block in st.session_state["blockchain"].chain:
            st.write(f"🧱 **Block #{block.index}**")
            st.write(f"📜 Transactions: {block.transactions}")
            st.write("---")
