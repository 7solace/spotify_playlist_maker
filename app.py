import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyOauthError
from spotipy.cache_handler import MemoryCacheHandler # Bellek tabanlı cache için eklendi

# --- Spotify API Kimlik Bilgileri ve Ayarları ---
CLIENT_ID = st.secrets.get("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = st.secrets.get("SPOTIPY_REDIRECT_URI") 
    
SCOPE = "playlist-modify-public playlist-modify-private"

# --- Spotify Kimlik Doğrulama Fonksiyonu (MemoryCacheHandler eklendi) ---
def get_spotify_oauth_manager():
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        print("HATA: API Kimlik bilgileri (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) Secrets'da eksik veya okunamadı!")
        return None 
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI, 
        scope=SCOPE,
        cache_handler=MemoryCacheHandler() # <<<< YENİ: Dosya yerine bellekte cache tut
    )

# --- Playlist Oluşturma ve Şarkı Arama Fonksiyonları (İçerikleri aynı) ---
def create_spotify_playlist_with_tracks(sp, tracks_to_add, playlist_name, public=True, description="Streamlit ile oluşturuldu"):
    if not tracks_to_add:
        st.warning("Playliste eklenecek şarkı bulunamadı.")
        return None
    try:
        user_id = sp.me()["id"] 
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=public, description=description)
        playlist_id = playlist["id"]
        playlist_url = playlist["external_urls"]["spotify"]
        track_uris = [track["uri"] for track in tracks_to_add if track.get("uri")]
        if not track_uris:
            st.warning("Eklenecek geçerli şarkı URI'si bulunamadı.")
            return playlist_url 
        sp.playlist_add_items(playlist_id, track_uris)
        st.success(f"'{playlist_name}' adında playlist başarıyla oluşturuldu!")
        st.link_button("🔗 Oluşturulan Playlisti Spotify'da Aç", playlist_url, use_container_width=True, type="primary")
        return playlist_url
    except Exception as e:
        st.error(f"Spotify playlisti oluşturulurken veya şarkılar eklenirken hata: {e}")
        st.exception(e)
        return None

def spotify_sarki_ara_ve_goster(sp, muzik_turu, sarki_sayisi, sanatci_adi_str):
    info_mesaji = f"Spotify'da"
    if muzik_turu: info_mesaji += f" '{muzik_turu.capitalize()}' türünde"
    if sanatci_adi_str:
        sanatci_temiz = sanatci_adi_str.strip()
        if muzik_turu and sanatci_temiz: info_mesaji += ","
        if sanatci_temiz: info_mesaji += f" sanatçı: {sanatci_temiz.title()} için" 
    info_mesaji += f" {sarki_sayisi} şarkı aranıyor..."
    query_parts = []
    if muzik_turu: query_parts.append(f"genre:\"{muzik_turu.strip()}\"")
    if sanatci_adi_str: query_parts.append(f"artist:\"{sanatci_adi_str.strip()}\"")
    if not query_parts:
        st.warning("Arama yapmak için lütfen en az bir müzik türü veya sanatçı adı girin.")
        return []
    query = " ".join(query_parts)
    st.info(f"Gönderilen sorgu: {query}")

    try:
        results = sp.search(q=query, type='track', limit=sarki_sayisi) 
        tracks = results.get('tracks', {}).get('items', [])
        if not tracks:
            st.warning("Belirttiğiniz kriterlere uygun şarkı Spotify'da bulunamadı.")
            return [] 
        st.subheader("🎶 Bulunan Şarkılar (Playlist'e Eklenmek Üzere): 🎶")
        for i, track_item in enumerate(tracks):
            sarki_adi = track_item.get('name', 'Bilinmeyen Şarkı')
            sanatcilar_list_api = [artist.get('name', 'Bilinmeyen Sanatçı') for artist in track_item.get('artists', [])]
            sanatcilar_gosterim = ", ".join(sanatcilar_list_api)
            album_data = track_item.get('album', {})
            album_adi = album_data.get('name', 'Bilinmeyen Albüm')
            spotify_url = track_item.get('external_urls', {}).get('spotify', '')
            album_images = album_data.get('images', [])
            album_art_url = None
            if album_images:
                if len(album_images) > 1: album_art_url = album_images[1]['url'] 
                elif len(album_images) == 1: album_art_url = album_images[0]['url'] 
            col_art, col_info = st.columns([1, 3]) 
            with col_art:
                if album_art_url: st.image(album_art_url, width=100) 
                else: st.caption("(Kapak yok)") 
            with col_info:
                st.markdown(f"**{i+1}. {sarki_adi}**")
                st.write(f"**Sanatçı(lar):** {sanatcilar_gosterim}")
                st.write(f"**Albüm:** {album_adi}")
                if spotify_url: st.markdown(f"   [Şarkıyı Spotify'da Dinle]({spotify_url})")
            st.write("---")
        return tracks 
    except Exception as e:
        st.error(f"Spotify'dan şarkı ararken bir hata oluştu: {e}")
        st.exception(e) 
        return []

# --- Streamlit Arayüzü Başlangıcı ---
st.set_page_config(page_title="Playlist Oluşturucu", page_icon="🎶", layout="centered")
# Başlık ve alt başlık markdown ile ortalandı
st.markdown(""" 
<div style="text-align: center;">
    <h1>🎶 Spotify Playlist Oluşturucu 🎶</h1>
    <p>Sevdiğin türe ve sanatçıya göre şarkıları bul ve <b>otomatik olarak Spotify playlisti oluştur!</b></p>
</div>
<br>
""", unsafe_allow_html=True)

# API Anahtarları ve OAuth Yöneticisi Kontrolü
if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    st.error("Spotify API anahtarları (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) Streamlit Secrets'da ayarlanmamış veya okunamadı! Lütfen uygulamanın Streamlit Cloud ayarlarından kontrol edin.")
    st.stop()

try:
    sp_oauth = get_spotify_oauth_manager() 
    if sp_oauth is None: 
        st.error("Spotify OAuth ayarları başlatılamadı. API anahtarları (Secrets) doğru girildi mi?")
        st.stop()
except Exception as e_oauth_init:
    st.error(f"Spotify OAuth başlatılırken kritik hata: {e_oauth_init}")
    st.exception(e_oauth_init)
    st.stop()

# Session state'leri başlat/kontrol et
if 'token_info' not in st.session_state:
    st.session_state.token_info = None # Başlangıçta token yok
if 'auth_url_displayed' not in st.session_state: # Auth linkinin gösterilip gösterilmediğini takip et
    st.session_state.auth_url_displayed = False

# OAuth Callback (URL'den 'code' alma) Mantığı
try:
    auth_code = st.query_params.get("code")
except AttributeError: 
    query_params_experimental = st.experimental_get_query_params()
    auth_code = query_params_experimental.get("code", [None])[0]

if auth_code:
    # Bu blok sadece URL'de 'code' varsa ve token daha önce bu 'code' ile alınmadıysa çalışmalı
    if not st.session_state.get('token_info_from_code_' + auth_code): # Aynı kodla tekrar token almayı engelle
        st.write(f"DEBUG: URL'de yetkilendirme kodu bulundu, token alınıyor...") 
        try:
            token_info = sp_oauth.get_access_token(auth_code, check_cache=False) # Cache'i zorlama
            st.session_state.token_info = token_info
            st.session_state['token_info_from_code_' + auth_code] = True # Bu kodu işlediğimizi işaretle
            st.session_state.auth_url_displayed = False # Auth linki artık gösterilmesin
            try: 
                st.query_params.clear()
            except AttributeError:
                st.experimental_set_query_params()
            st.success("Spotify kimlik doğrulaması başarılı!")
            st.rerun() # Sayfayı temiz bir şekilde yeniden yükle ve doğru arayüzü göster
        except Exception as e:
            st.error(f"Spotify token alınırken hata: {e}")
            st.exception(e)
            st.session_state.token_info = None
# OAuth Callback Sonu

# Arayüzün Ana Mantığı
if st.session_state.token_info and not sp_oauth.is_token_expired(st.session_state.token_info):
    # KULLANICI GİRİŞ YAPMIŞ
    sp = spotipy.Spotify(auth=st.session_state.token_info['access_token'])
    try:
        user_info = sp.me()
        st.success(f"Hoş geldin, {user_info.get('display_name', 'kullanıcı')}! Spotify'a bağlısın.")
    except Exception as e:
        st.warning("Spotify bağlantınızda bir sorun oluştu. Lütfen tekrar bağlanın.")
        st.session_state.token_info = None # Token'ı temizle
        st.session_state.auth_url_displayed = False
        # Hata durumunda tekrar login için bir buton veya direkt rerun ile login ekranına yönlendirme
        if st.button("Bağlantı Sorunu - Tekrar Bağlan"):
            st.rerun() 
        st.stop()

    with st.form("playlist_form"):
        st.subheader("Yeni Playlist Oluştur")
        muzik_turu = st.text_input("Hangi türde şarkılar istersiniz?", placeholder="örn: Pop, Rock, Trap")
        sarki_sayisi_st = st.number_input("Kaç şarkı bulunsun ve playliste eklensin?", min_value=1, max_value=30, value=5)
        istege_bagli_sanatci_st = st.text_input("Belirli bir sanatçı var mı?", placeholder="örn: Tarkan") 
        yeni_playlist_adi = st.text_input("Oluşturulacak Spotify Playlistinin Adı Ne Olsun?", f"{muzik_turu.capitalize() if muzik_turu else 'Yeni'} Streamlit Playlistim")
        submitted_search_and_create = st.form_submit_button("🎵 Şarkıları Bul ve Spotify Playlisti Oluştur")

    if submitted_search_and_create:
        if not muzik_turu and not istege_bagli_sanatci_st: 
            st.warning("Lütfen bir müzik türü veya bir sanatçı adı girin.")
        elif not yeni_playlist_adi:
            st.warning("Lütfen oluşturulacak playlist için bir ad girin.")
        else:
            with st.spinner("Şarkılar aranıyor ve playlist oluşturuluyor... Lütfen bekleyin... ⏳"):
                tracks_found = spotify_sarki_ara_ve_goster(sp, muzik_turu, int(sarki_sayisi_st), istege_bagli_sanatci_st)
                if tracks_found:
                    create_spotify_playlist_with_tracks(sp, tracks_found, yeni_playlist_adi)
    
    if st.button("Spotify Bağlantısını Kes", type="secondary"):
        st.session_state.token_info = None
        st.session_state.pop('token_info_from_code_' + auth_code, None) # İşlenmiş kodu temizle
        st.session_state.auth_url_displayed = False
        try: 
            st.query_params.clear()
        except AttributeError:
            st.experimental_set_query_params()
        st.rerun()
else:
    # KULLANICI GİRİŞ YAPMAMIŞ: Giriş Ekranını Göster
    if not st.session_state.auth_url_displayed: # Eğer auth linki daha önce gösterilmediyse
        st.write("") 
        _, col_content, _ = st.columns([0.5, 2, 0.5]) 
        with col_content: 
            st.markdown(f"""<div style="display: flex; justify-content: center; margin-bottom: 10px;"><img src="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png" alt="Spotify Logo" width="100"></div>""", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center; margin-bottom: 10px;'>Spotify Hesabınla Bağlan</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; margin-bottom: 20px;'>Harika çalma listeleri oluşturmak ve müzik dünyasına dalmak için Spotify hesabınla giriş yapman gerekiyor.</p>", unsafe_allow_html=True)
            try:
                auth_url = sp_oauth.get_authorize_url()
                # Buton yerine direkt link_button kullanıyoruz, bu zaten yönlendirme yapar.
                # Eğer butona basınca yönlendirme isteniyorsa, state ile yönetmek gerekir.
                # Şimdilik direkt link daha basit.
                if st.link_button("🔗 Spotify ile Bağlan ve Başla!", auth_url, use_container_width=True, type="primary"):
                    st.session_state.auth_url_displayed = True # Link gösterildi ve tıklandı (varsayım)
                    # Tarayıcı yönleneceği için Streamlit script'i durmaz, ama kullanıcı yeni sayfaya gider.
                    # Geri döndüğünde yukarıdaki auth_code bloğu çalışır.
                st.markdown("<p style='text-align: center; font-size: 0.9em; opacity: 0.8; margin-top: 10px;'>Bu linke tıkladığında Spotify giriş sayfasına yönlendirileceksin. İzinleri verdikten sonra otomatik olarak uygulamaya geri döneceksin ve kullanmaya başlayabileceksin.</p>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Spotify yetkilendirme linki oluşturulurken bir sorun oluştu: {e}")
                st.exception(e)
            st.markdown("<hr style='margin-top: 30px; margin-bottom: 20px; border-color: #333;'>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 1.1em; font-style: italic; color: #A0A0A0;'>🎧 Ruh haline göre çalsın, sen keyfine bak!</p>", unsafe_allow_html=True)
    # Eğer auth_url_displayed True ise, kullanıcı linke tıklamış ve Spotify'a yönlenmiş demektir.
    # Geri dönüşünü (URL'de code ile) yukarıdaki auth_code bloğu yakalayacak.
    # Bu arada kullanıcıya bir bekleme mesajı gösterilebilir.
    elif st.session_state.auth_url_displayed and not auth_code:
         st.info("Spotify'dan geri yönlendiriliyorsunuz... Lütfen bekleyin veya sayfa yüklenmezse yenileyin.")


# --- Sidebar ---
st.sidebar.header("Nasıl Kullanılır?")
st.sidebar.info(
    "1. 'Spotify ile Bağlan' linkine tıklayarak giriş yapın ve izin verin.\n"
    "2. Sayfa yenilendikten sonra formu doldurun.\n"
    "3. 'Şarkıları Bul ve Spotify Playlisti Oluştur' butonuna tıklayın.\n"
    "4. Playlistiniz Spotify hesabınızda oluşturulacak ve linki burada gösterilecektir."
)
st.sidebar.markdown("---")
st.sidebar.subheader("Geliştirici")
st.sidebar.markdown("👾 Discord: **7grizi**") 
st.sidebar.markdown("---")
st.sidebar.subheader("✨ Geliştiricinin Ruh Hali ✨")
st.sidebar.markdown("🎶 **Feel It** (Invincible)") 
st.sidebar.markdown("---")
st.sidebar.caption(f"© {2025} Playlist Oluşturucu")
