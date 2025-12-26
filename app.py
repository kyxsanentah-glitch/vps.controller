import streamlit as st
import digitalocean
import time
import random
import string
from digitalocean import Manager

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Kyxzan VPS Deployer",
    page_icon="⚡",
    layout="wide"
)

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    div[data-testid="stExpander"] { background-color: #1e1e1e; border: 1px solid #333; }
    h1 { color: #00e5ff; } 
    .success-text { color: #00ff00; font-weight: bold; }
    /* Style untuk status login di sidebar */
    .login-box { padding: 15px; background-color: #1c2e2e; border-radius: 10px; border: 1px solid #00e5ff; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Kyxzan VPS Auto-Controller")
st.markdown("Controller Vps By Kyxzan")

# ==========================================
# BAGIAN AUTHENTICATION (SESSION STATE)
# ==========================================
if 'do_token' not in st.session_state:
    st.session_state.do_token = ''

with st.sidebar:
    st.header("🔐 User Authentication")
    
    # Cek apakah user sudah simpan token atau belum
    if not st.session_state.do_token:
        st.info("Masukkan API Token DigitalOcean Anda untuk memulai sesi.")
        
        # Form Input Token
        with st.form("auth_form"):
            input_token = st.text_input("DigitalOcean API Token", type="password", help="Token disimpan sementara di browser.")
            btn_login = st.form_submit_button("💾 Simpan & Masuk", type="primary")
            
            if btn_login:
                if input_token:
                    st.session_state.do_token = input_token
                    st.rerun()
                else:
                    st.error("Token tidak boleh kosong!")
    else:
        # Tampilan jika sudah Login
        st.markdown("""
        <div class='login-box'>
            <small>Status:</small><br>
            <b style='color:#00ff00'>✅ TERHUBUNG</b><br>
            <small>Session Active</small>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout / Ganti Token"):
            st.session_state.do_token = ''
            st.rerun()

# Logic Utama: Stop jika tidak ada token
if not st.session_state.do_token:
    st.warning("⬅️ Silakan Login / Masukkan API Token di Sidebar sebelah kiri.")
    st.stop()

# Gunakan token dari session state
api_token = st.session_state.do_token

# Inisialisasi Manager
try:
    manager = digitalocean.Manager(token=api_token)
except Exception as e:
    st.sidebar.error("❌ Token Invalid")
    st.error(f"Gagal terhubung: {e}")
    st.session_state.do_token = ''
    st.stop()

# --- DATA LENGKAP ---

# 1. Region Lengkap
REGIONS = {
    "🇸🇬 Singapore (SGP1)": "sgp1",
    "🇺🇸 New York 1 (NYC1)": "nyc1",
    "🇺🇸 New York 3 (NYC3)": "nyc3",
    "🇺🇸 San Francisco 3 (SFO3)": "sfo3",
    "🇳🇱 Amsterdam 3 (AMS3)": "ams3",
    "🇬🇧 London 1 (LON1)": "lon1",
    "🇩🇪 Frankfurt 1 (FRA1)": "fra1",
    "🇨🇦 Toronto 1 (TOR1)": "tor1",
    "🇮🇳 Bangalore 1 (BLR1)": "blr1",
    "🇦🇺 Sydney 1 (SYD1)": "syd1"
}

# 2. Size Lengkap (PREMIUM AMD NVMe)
SIZES = {
    "🔥 AMD 1 GB / 1 vCPU": "s-1vcpu-1gb-amd",
    "🔥 AMD 2 GB / 1 vCPU": "s-1vcpu-2gb-amd",
    "🔥 AMD 2 GB / 2 vCPU": "s-2vcpu-2gb-amd",
    "🔥 AMD 4 GB / 2 vCPU": "s-2vcpu-4gb-amd",
    "🔥 AMD 8 GB / 2 vCPU": "s-2vcpu-8gb-amd",
    "🔥 AMD 8 GB / 4 vCPU": "s-4vcpu-8gb-amd",
    "🔥 AMD 16 GB / 4 vCPU": "s-4vcpu-16gb-amd",
    "🔥 AMD 16 GB / 8 vCPU": "s-8vcpu-16gb-amd"
}

IMAGES = {
    "Ubuntu 22.04 LTS": "ubuntu-22-04-x64",
    "Ubuntu 20.04 LTS": "ubuntu-20-04-x64",
    "Debian 11": "debian-11-x64",
    "CentOS Stream 9": "centos-stream-9-x64"
}

# --- GENERATOR PASSWORD KYXZAN ---
def generate_kyxzan_pass():
    chars = string.ascii_letters + string.digits + "!@#$%"
    suffix = ''.join(random.choices(chars, k=6))
    return f"Kyxzan{suffix}"

# --- TABS ---
tab_create, tab_list = st.tabs(["🚀 Auto Create", "📋 Manage your Droplet"])

# ==========================================
# TAB 1: CREATE VPS (AUTO PASS)
# ==========================================
with tab_create:
    st.subheader("Deploy Premium AMD Droplet")
    
    with st.form("deploy_auto"):
        c1, c2 = st.columns(2)
        with c1:
            name_input = st.text_input("Nama Host", "kyxzan-server")
            region_key = st.selectbox("Lokasi Server", list(REGIONS.keys()))
            st.info("🔒 Password otomatis Dibuat")
        
        with c2:
            image_key = st.selectbox("Operating System", list(IMAGES.keys()))
            size_key = st.selectbox("Spesifikasi (AMD NVMe)", list(SIZES.keys()))
        
        btn_deploy = st.form_submit_button("🔥 Create VPS Now", type="primary")

    if btn_deploy:
        auto_pass = generate_kyxzan_pass()
        
        sel_region = REGIONS[region_key]
        sel_image = IMAGES[image_key]
        sel_size = SIZES[size_key]
        
        user_data = f"""#cloud-config
chpasswd:
  list: |
    root:{auto_pass}
  expire: False
ssh_pwauth: True
"""

        status_container = st.status("🚀 Sedang memproses...", expanded=True)
        
        try:
            status_container.write(f"🔐 Password digenerate: {auto_pass}")
            status_container.write("📡 Request ke DigitalOcean...")
            
            droplet = digitalocean.Droplet(
                token=api_token,
                name=name_input,
                region=sel_region,
                image=sel_image,
                size_slug=sel_size,
                user_data=user_data,
                backups=False
            )
            droplet.create()
            
            status_container.write("⏳ Menunggu IP Address (max 60 detik)...")
            
            max_retries = 20
            got_ip = False
            final_ip = "Unknown"
            
            bar = status_container.progress(0)
            
            for i in range(max_retries):
                time.sleep(3)
                droplet.load()
                
                bar.progress((i + 1) * 5)
                
                if droplet.ip_address:
                    final_ip = droplet.ip_address
                    got_ip = True
                    bar.progress(100)
                    break
            
            status_container.update(label="✅ Selesai!", state="complete", expanded=False)

            if got_ip:
                st.success(f"Server {name_input} Siap!")
                st.markdown("### 🎫 DATA LOGIN VPS (Copy!)")
                
                login_text = f"""
================================
IP ADDRESS : {final_ip}
USERNAME   : root
PORT       : 22
PASSWORD   : {auto_pass}
================================
LOGIN PAKAI APPS TERMIUS ADA DI PLAYSTORE
"""
                st.code(login_text, language="bash")
                st.caption("⚠️ Simpan password ini sekarang. Web tidak menyimpannya.")
            else:
                st.warning("VPS Created tapi IP belum muncul. Cek tab List.")

        except Exception as e:
            status_container.update(label="❌ Error", state="error")
            st.error(f"Terjadi kesalahan: {e}")

# ==========================================
# TAB 2: MANAGE & REBUILD (FITUR BARU)
# ==========================================
with tab_list:
    st.subheader("Active Droplets Manager")
    if st.button("🔄 Refresh Data List"):
        st.rerun()

    try:
        droplets = manager.get_all_droplets()
    except Exception as e:
        st.error(f"Gagal mengambil data: {e}")
        droplets = []

    if not droplets:
        st.info("Tidak ada VPS aktif saat ini.")
    
    for d in droplets:
        # Tampilan Expandable per VPS
        with st.expander(f"🖥️ {d.name}  |  IP: {d.ip_address}  |  {d.status}"):
            
            # --- Bagian Atas: Informasi ---
            col_info, col_act = st.columns([1, 2])
            
            with col_info:
                st.markdown("**Detail Server:**")
                st.code(f"""
Region : {d.region['slug']}
Image  : {d.image['slug']}
Size   : {d.size_slug}
ID     : {d.id}
                """)
            
            with col_act:
                st.markdown("**⚡ Control Panel:**")
                
                # Baris Tombol Action
                b1, b2, b3 = st.columns(3)
                
                with b1:
                    if st.button("🔄 Reboot", key=f"reb_{d.id}"):
                        d.reboot()
                        st.toast(f"{d.name} sedang direstart...")
                
                with b2:
                    if st.button("🔌 Power Off", key=f"off_{d.id}"):
                        d.shutdown()
                        st.toast(f"Mematikan {d.name}...")

                with b3:
                    if st.button("🗑️ DELETE", type="primary", key=f"del_{d.id}"):
                        d.destroy()
                        st.error(f"VPS {d.name} Dihapus Permanen!")
                        time.sleep(1)
                        st.rerun()
                
                st.divider()
                
                # --- Bagian Rebuild (Install Ulang OS) ---
                st.markdown("**⚠️ Rebuild OS (Reset VPS)**")
                st.caption("Pilih OS baru dibawah ini, lalu klik Rebuild. Data lama akan hilang.")
                
                rb_col1, rb_col2 = st.columns([2, 1])
                
                with rb_col1:
                    # Dropdown pilih OS untuk rebuild
                    target_image_name = st.selectbox("Pilih OS Baru:", list(IMAGES.keys()), key=f"sel_rb_{d.id}")
                
                with rb_col2:
                    # Tombol Eksekusi Rebuild
                    if st.button("🔥 REBUILD", key=f"btn_rb_{d.id}"):
                        try:
                            target_slug = IMAGES[target_image_name]
                            d.rebuild(image=target_slug)
                            st.success(f"Proses Rebuild ke {target_image_name} dimulai!")
                        except Exception as e:
                            st.error(f"Gagal Rebuild: {e}")

