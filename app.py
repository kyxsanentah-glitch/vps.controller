import streamlit as st
import digitalocean
from digitalocean import Manager

# --- KONFIGURASI HALAMAN WEB ---
st.set_page_config(
    page_title="DO AMD Controller",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS biar tampilan lebih mirip Web App Admin
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; }
    .reportview-container { background: #0e1117; }
    div[data-testid="stExpander"] { border: 1px solid #30333F; border-radius: 8px; }
    h1, h2, h3 { color: #0080ff; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Digital Ocean VPS Controller")
st.markdown("Web Panel khusus manajemen DigitalOcean Droplet (Premium)")

# --- SIDEBAR: AUTHENTICATION ---
with st.sidebar:
    st.header("🔐 API Access")
    api_token = st.text_input("DigitalOcean API Token", type="password", help="Masukkan token Read/Write dari dashboard DO")
    
    st.info("💡 Data list region & size di-hardcode agar loading web cepat.")
    
    if st.button("Refresh Halaman"):
        st.rerun()

if not api_token:
    st.warning("⚠️ Masukkan API Token di sidebar sebelah kiri untuk mulai mengontrol VPS.")
    st.stop()

# Fungsi koneksi ke DO
def get_manager():
    return digitalocean.Manager(token=api_token)

manager = get_manager()

# --- DATA LIST LENGKAP (PREMIUM AMD & REGIONS) ---
# Daftar Region Lengkap DigitalOcean
REGIONS = {
    "Singapore (SGP1)": "sgp1",
    "New York 1 (NYC1)": "nyc1",
    "New York 3 (NYC3)": "nyc3",
    "San Francisco 3 (SFO3)": "sfo3",
    "Amsterdam 3 (AMS3)": "ams3",
    "London 1 (LON1)": "lon1",
    "Frankfurt 1 (FRA1)": "fra1",
    "Toronto 1 (TOR1)": "tor1",
    "Bangalore 1 (BLR1)": "blr1",
    "Sydney 1 (SYD1)": "syd1"
}

# Daftar Size Khusus Premium AMD (Sesuai request: kecil s/d 16GB/8vCPU)
# Slug DO untuk Premium AMD biasanya diakhiri dengan '-amd' atau '-premium-amd' (tergantung region, pakai basic AMD slug)
SIZES_AMD = {
    "AMD 1 GB / 1 vCPU ($7/mo)": "s-1vcpu-1gb-amd",
    "AMD 2 GB / 1 vCPU ($14/mo)": "s-1vcpu-2gb-amd",
    "AMD 4 GB / 2 vCPU ($28/mo)": "s-2vcpu-4gb-amd",
    "AMD 8 GB / 4 vCPU ($56/mo)": "s-4vcpu-8gb-amd",
    "AMD 16 GB / 8 vCPU ($112/mo)": "s-8vcpu-16gb-amd" 
}

# Daftar OS Populer
IMAGES = {
    "Ubuntu 22.04 (LTS)": "ubuntu-22-04-x64",
    "Ubuntu 20.04 (LTS)": "ubuntu-20-04-x64",
    "Debian 11": "debian-11-x64",
    "CentOS Stream 9": "centos-stream-9-x64",
    "Rocky Linux 9": "rockylinux-9-x64"
}

# --- TABS UTAMA ---
tab1, tab2 = st.tabs(["📋 List VPS & Control", "➕ Create New VPS"])

# --- TAB 1: LIST & MANAGE ---
with tab1:
    st.header("Daftar VPS Aktif")
    
    try:
        my_droplets = manager.get_all_droplets()
    except Exception as e:
        st.error(f"Gagal konek ke DigitalOcean: {e}")
        st.stop()

    if not my_droplets:
        st.info("Belum ada VPS yang aktif. Silakan buat di tab sebelah 👉")

    for droplet in my_droplets:
        # Tampilan Card per VPS
        with st.expander(f"🖥️ {droplet.name} | {droplet.ip_address or 'Pending IP...'}", expanded=True):
            col_info, col_act1, col_act2 = st.columns([2, 1, 1])
            
            with col_info:
                st.write(f"**Status:** `{droplet.status}`")
                st.write(f"**Spec:** `{droplet.size_slug}` | **Region:** `{droplet.region['slug']}`")
                st.write(f"**Image:** `{droplet.image['slug']}`")
                st.write(f"**ID:** `{droplet.id}`")

            with col_act1:
                st.write("##### Power Actions")
                if st.button("🔄 Reboot", key=f"btn_reb_{droplet.id}"):
                    droplet.reboot()
                    st.toast(f"Perintah Reboot dikirim ke {droplet.name}!")
                
                # Fitur Rebuild
                rebuild_img = st.selectbox("OS Rebuild", list(IMAGES.keys()), key=f"sel_reb_{droplet.id}")
                if st.button("⚠️ Rebuild OS", key=f"btn_rebuild_{droplet.id}"):
                    if st.checkbox(f"Yakin reset {droplet.name}?", key=f"chk_reb_{droplet.id}"):
                        try:
                            droplet.rebuild(image=IMAGES[rebuild_img])
                            st.toast(f"Proses Rebuild dimulai untuk {droplet.name}...")
                        except Exception as e:
                            st.error(f"Gagal Rebuild: {e}")

            with col_act2:
                st.write("##### Danger Zone")
                if st.button("🛑 Shutdown", key=f"btn_shut_{droplet.id}"):
                    droplet.shutdown()
                    st.toast(f"Perintah Shutdown dikirim ke {droplet.name}")
                
                st.write("") # Spacer
                if st.button("🗑️ DELETE PERMANENT", key=f"btn_del_{droplet.id}", type="primary"):
                    # Double check pakai checkbox biar gak kepencet
                    st.warning("Tekan sekali lagi tombol di bawah untuk konfirmasi")
                    if st.checkbox("Saya sadar data akan hilang", key=f"chk_del_{droplet.id}"):
                        droplet.destroy()
                        st.success(f"VPS {droplet.name} telah dihapus!")
                        st.rerun()

# --- TAB 2: CREATE NEW VPS ---
with tab2:
    st.header("Deploy Premium AMD Droplet")
    
    with st.form("deploy_form"):
        c1, c2 = st.columns(2)
        with c1:
            name_input = st.text_input("Nama VPS", placeholder="server-vip-01")
            region_key = st.selectbox("Pilih Region", list(REGIONS.keys()))
        
        with c2:
            image_key = st.selectbox("Pilih OS", list(IMAGES.keys()))
            size_key = st.selectbox("Pilih Spesifikasi (AMD Premium)", list(SIZES_AMD.keys()))
        
        st.caption("Note: Password root akan dikirim ke email akun DigitalOcean kamu jika tidak setting SSH Key.")
        
        submitted = st.form_submit_button("🚀 Deploy Sekarang", type="primary")
        
        if submitted:
            if not name_input:
                st.error("Nama VPS wajib diisi!")
            else:
                try:
                    # Ambil value asli dari key dictionary
                    selected_region = REGIONS[region_key]
                    selected_image = IMAGES[image_key]
                    selected_size = SIZES_AMD[size_key]
                    
                    new_droplet = digitalocean.Droplet(
                        token=api_token,
                        name=name_input,
                        region=selected_region,
                        image=selected_image,
                        size_slug=selected_size,
                        backups=False
                    )
                    
                    with st.spinner('Sedang menghubungi DigitalOcean...'):
                        new_droplet.create()
                    
                    st.success(f"Berhasil! VPS **{name_input}** sedang dibuat di **{selected_region}**.")
                    st.balloons()
                    st.info("Silakan pindah ke tab 'List VPS' dan refresh setelah 1 menit untuk melihat IP.")
                    
                except digitalocean.DataReadError as e:
                    st.error(f"Error API: {e} (Cek apakah Token valid / Saldo cukup?)")
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

