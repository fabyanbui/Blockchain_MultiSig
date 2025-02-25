import streamlit as st
import time
from blockchain import Blockchain

# --- Khởi tạo Session State ---
if "users" not in st.session_state:
    st.session_state["users"] = {}

if "multisig_wallets" not in st.session_state:
    st.session_state["multisig_wallets"] = {}

if "blockchain" not in st.session_state:
    st.session_state["blockchain"] = Blockchain()

if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

# === Sidebar: Đăng nhập / Đăng ký / Đăng xuất ===
with st.sidebar:
    st.header("🔐 Đăng nhập / Đăng ký")
    username = st.text_input("Tên tài khoản")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Đăng ký"):
            if username and username not in st.session_state["users"]:
                st.session_state["users"][username] = {"wallets": []}
                st.success("✅ Đăng ký thành công!")
            else:
                st.warning("⚠ Tài khoản đã tồn tại hoặc không hợp lệ!")

    with col2:
        if st.button("Đăng nhập"):
            if username in st.session_state["users"]:
                st.session_state["current_user"] = username
                st.success(f"✅ Đăng nhập thành công! Xin chào **{username}**")
            else:
                st.error("❌ Tài khoản không tồn tại! Vui lòng đăng ký trước.")

    current_user = st.session_state["current_user"]
    if current_user:
        st.write(f"👤 **Tài khoản hiện tại:** {current_user}")
        if st.button("🚪 Đăng xuất"):
            st.session_state["current_user"] = None
            st.experimental_rerun()

# === Kiểm tra đăng nhập ===
if not st.session_state["current_user"]:
    st.warning("⚠ Vui lòng đăng nhập để tiếp tục!")
    st.stop()

# === Giao diện chính ===
st.title("🏦 Ví MultiSig Blockchain")

# --- Quản lý Ví MultiSig ---
st.header("📌 Quản lý Ví MultiSig")

wallet_name = st.text_input("Nhập tên ví MultiSig mới")
if st.button("Tạo Ví MultiSig"):
    if wallet_name and wallet_name not in st.session_state["multisig_wallets"]:
        st.session_state["multisig_wallets"][wallet_name] = {
            "owners": [current_user],  
            "transactions": [],
            "threshold": 2
        }
        st.session_state["users"][current_user]["wallets"].append(wallet_name)
        st.success(f"✅ Ví '{wallet_name}' đã được tạo!")
    else:
        st.warning("⚠ Tên ví đã tồn tại hoặc không hợp lệ!")

# Hiển thị danh sách ví
user_wallets = st.session_state["users"].get(current_user, {}).get("wallets", [])
selected_wallet = st.selectbox("🔑 Chọn Ví MultiSig", user_wallets if user_wallets else ["Chưa có ví"])

if selected_wallet != "Chưa có ví":
    wallet = st.session_state["multisig_wallets"][selected_wallet]

    # --- Quản lý Chủ sở hữu ---
    st.subheader(f"👥 Chủ sở hữu Ví '{selected_wallet}'")

    new_owner = st.text_input("Thêm địa chỉ đồng ký (tài khoản đã đăng ký)")
    if st.button("Thêm Chủ sở hữu"):
        if new_owner in st.session_state["users"]:
            if new_owner not in wallet["owners"]:
                wallet["owners"].append(new_owner)
                st.session_state["users"][new_owner]["wallets"].append(selected_wallet)
                st.success(f"✅ Đã thêm {new_owner} vào Ví '{selected_wallet}'")
            else:
                st.warning("⚠ Người này đã là đồng ký!")
        else:
            st.error("❌ Tài khoản không tồn tại!")

    st.write(f"🔑 **Chủ sở hữu hiện tại:** {wallet['owners']}")
    max_signatures = max(1, len(wallet["owners"]))
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

    for i, txn in enumerate(wallet["transactions"]):
        st.write(f"🔹 **Giao dịch #{i}:** {txn}")
        if current_user in wallet["owners"]:
            if st.button(f"Ký giao dịch #{i}", key=f"sign_{i}"):
                if current_user not in txn["signatures"]:
                    txn["signatures"].append(current_user)
                    wallet["transactions"][i] = txn  
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
        with st.expander(f"🧱 Block #{block.index}"):
            st.write(f"📅 **Thời gian:** {time.ctime(block.timestamp)}")
            st.write(f"🔗 **Hash:** {block.hash}")
            st.write(f"🔗 **Previous Hash:** {block.previous_hash}")
            st.write(f"📜 **Transactions:** {block.transactions}")
            st.write(f"⚡ **Nonce:** {block.nonce}")
