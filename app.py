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
</style>
""", unsafe_allow_html=True)

st.title("⚡ Kyxzan VPS Auto-Controller")
st.markdown("Create VPS Premium AMD & **Auto Generate Kyxzan Password**")

# --- SIDEBAR: AUTH ---
with st.sidebar:
    st.header("🔑 API Configuration")
    api_token = st.text_input("DigitalOcean Token", type="password")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()

if not api_token:
    st.warning("⚠️ Masukkan API Token dulu.")
    st.stop()

# Inisialisasi Manager
try:
    manager = digitalocean.Manager(token=api_token)
except:
    st.error("Token invalid.")
    st.stop()

# --- DATA LENGKAP (REGION & SIZE) ---

# 1. Region Lengkap DigitalOcean
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

# 2. Size Lengkap (Fokus Premium AMD NVMe + 1 Regular Murah)
SIZES = {
    "🔥 AMD Premium 1 GB / 1 vCPU ($7)": "s-1vcpu-1gb-amd",
    "🔥 AMD Premium 2 GB / 1 vCPU ($14)": "s-1vcpu-2gb-amd",
    "🔥 AMD Premium 4 GB / 2 vCPU ($28)": "s-2vcpu-4gb-amd",
    "🔥 AMD Premium 8 GB / 4 vCPU ($56)": "s-4vcpu-8gb-amd",
    "🔥 AMD Premium 16 GB / 8 vCPU ($112)": "s-8vcpu-16gb-amd",
    "🐌 Regular Intel 1 GB / 1 vCPU ($6)": "s-1vcpu-1gb" # Opsi Hemat
}

IMAGES = {
    "Ubuntu 22.04 LTS": "ubuntu-22-04-x64",
    "Ubuntu 20.04 LTS": "ubuntu-20-04-x64",
    "Debian 11": "debian-11-x64",
    "CentOS Stream 9": "centos-stream-9-x64"
}

# --- GENERATOR PASSWORD KYXZAN ---
def generate_kyxzan_pass():
    # Format: Kyxzan + 5 karakter acak (Angka & Simbol) biar aman
    chars = string.ascii_letters + string.digits + "!@#$%"
    suffix = ''.join(random.choices(chars, k=6))
    return f"Kyxzan{suffix}"

# --- TABS ---
tab_create, tab_list = st.tabs(["🚀 Auto Create", "📋 List VPS"])

# ==========================================
# TAB 1: CREATE VPS (AUTO PASS)
# ==========================================
with tab_create:
    st.subheader("Deploy New Droplet")
    
    with st.form("deploy_auto"):
        c1, c2 = st.columns(2)
        with c1:
            name_input = st.text_input("Nama Host", "kyxzan-server")
            region_key = st.selectbox("Lokasi Server", list(REGIONS.keys()))
            st.info("🔒 Password otomatis: **Kyxzan[Acak]**")
        
        with c2:
            image_key = st.selectbox("Operating System", list(IMAGES.keys()))
            size_key = st.selectbox("Spesifikasi", list(SIZES.keys()))
        
        btn_deploy = st.form_submit_button("🔥 Deploy & Generate Password", type="primary")

    if btn_deploy:
        # 1. Generate Password Otomatis
        auto_pass = generate_kyxzan_pass()
        
        # 2. Persiapan Data
        sel_region = REGIONS[region_key]
        sel_image = IMAGES[image_key]
        sel_size = SIZES[size_key]
        
        # Script Cloud-Init (Inject Password)
        user_data = f"""#cloud-config
chpasswd:
  list: |
    root:{auto_pass}
  expire: False
ssh_pwauth: True
"""

        # 3. Proses Create
        status_container = st.status("🚀 Sedang memproses...", expanded=True)
        
        try:
            # STEP A: Request API
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
            
            # STEP B: Looping cek IP
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

            # STEP C: Hasil Akhir
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
# TAB 2: LIST VPS
# ==========================================
with tab_list:
    st.subheader("Active Droplets")
    if st.button("Refresh List"):
        st.rerun()

    try:
        droplets = manager.get_all_droplets()
    except:
        droplets = []

    if not droplets:
        st.write("Tidak ada VPS aktif.")
    
    for d in droplets:
        with st.expander(f"{d.name} ({d.ip_address})"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.code(f"IP: {d.ip_address}\nRegion: {d.region['slug']}\nSpecs: {d.size_slug}\nStatus: {d.status}")
            with c2:
                if st.button("🗑️ Hapus", key=f"del_{d.id}"):
                    d.destroy()
                    st.toast("VPS Dihapus!")
                    time.sleep(1)
                    st.rerun()
