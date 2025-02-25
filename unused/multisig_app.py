import streamlit as st
from ecdsa import SigningKey, SECP256k1
import hashlib

# Hàm tạo khóa cá nhân và địa chỉ
def generate_key_pair():
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.get_verifying_key()
    return private_key, public_key

# Hàm tạo địa chỉ từ public key
def generate_address(public_key):
    return hashlib.sha256(public_key.to_string()).hexdigest()

# Hàm tạo chữ ký
def sign_message(private_key, message):
    return private_key.sign(message.encode())

# Hàm xác minh chữ ký
def verify_signature(public_key, message, signature):
    return public_key.verify(signature, message.encode())

# Hàm tạo địa chỉ MultiSig
def create_multisig_address(public_keys, required_signatures):
    # Đơn giản hóa: kết hợp các public key và hash chúng
    combined_keys = b''.join([key.to_string() for key in public_keys])
    return hashlib.sha256(combined_keys).hexdigest()

# Giao diện Streamlit
st.title("MultiSig Wallet Demo")

# Tạo các khóa cá nhân và địa chỉ
st.sidebar.header("Tạo ví MultiSig")
num_signers = st.sidebar.number_input("Số lượng người ký", min_value=2, max_value=5, value=3)
required_signatures = st.sidebar.number_input("Số chữ ký cần thiết", min_value=1, max_value=num_signers, value=2)

private_keys = []
public_keys = []

for i in range(num_signers):
    st.sidebar.write(f"Người ký {i+1}")
    private_key, public_key = generate_key_pair()
    private_keys.append(private_key)
    public_keys.append(public_key)
    st.sidebar.write(f"Địa chỉ: {generate_address(public_key)}")

# Tạo địa chỉ MultiSig
multisig_address = create_multisig_address(public_keys, required_signatures)
st.sidebar.write(f"Địa chỉ MultiSig: {multisig_address}")

# Giao diện chính
st.header("Tạo giao dịch")
message = st.text_input("Nhập thông điệp cần ký")

if st.button("Tạo chữ ký"):
    signatures = []
    for i in range(num_signers):
        signature = sign_message(private_keys[i], message)
        signatures.append(signature)
        st.write(f"Chữ ký từ người ký {i+1}: {signature.hex()}")

    st.session_state.signatures = signatures

if st.button("Xác minh giao dịch"):
    if 'signatures' not in st.session_state:
        st.error("Chưa có chữ ký nào được tạo.")
    else:
        valid_signatures = 0
        for i in range(num_signers):
            if verify_signature(public_keys[i], message, st.session_state.signatures[i]):
                valid_signatures += 1
                st.write(f"Chữ ký từ người ký {i+1} hợp lệ.")
            else:
                st.write(f"Chữ ký từ người ký {i+1} không hợp lệ.")

        if valid_signatures >= required_signatures:
            st.success("Giao dịch hợp lệ và đã được xác nhận.")
        else:
            st.error("Giao dịch không hợp lệ, không đủ chữ ký.")
