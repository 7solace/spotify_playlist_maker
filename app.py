import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyOauthError

# --- Spotify API Kimlik Bilgileri ve Ayarları ---
CLIENT_ID = st.secrets.get("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = st.secrets.get("SPOTIPY_REDIRECT_URI") 
    
SCOPE = "playlist-modify-public playlist-modify-private"

# --- Spotify Kimlik Doğrulama Fonksiyonu ---
def get_spotify_oauth_manager(): # Adını değiştirdim, çünkü artık OAuth Manager döndürüyor
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        # Bu hata, aşağıdaki ana kontrol tarafından yakalanmalı ve kullanıcıya gösterilmeli.
        # Burada None döndürmek, ana kontrolün hatayı ele almasını sağlar.
        return None 
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI, 
        scope=SCOPE,
        # cache_path=None # Session state kullanacağız
        # open_browser=True (varsayılan)
    )

# --- Playlist Oluşturma ve Şarkı Arama Fonksiyonları (İçerikleri aynı, DEBUG'lar azaltıldı) ---
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
        st.link_button("🔗 Oluşturulan Playlisti Spotify'da Aç", playlist_url, use_container_width=True)
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
st.title("🎶 Spotify Playlist Oluşturucu 🎶")
st.markdown("Sevdiğin türe ve sanatçıya göre şarkıları bul ve **otomatik olarak Spotify playlisti oluştur!**")

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

# Session state'leri başlat
if 'token_info' not in st.session_state:
    st.session_state.token_info = sp_oauth.get_cached_token() # Başlangıçta önbelleği kontrol et

if 'spotify_client' not in st.session_state:
    st.session_state.spotify_client = None
    if st.session_state.token_info and not sp_oauth.is_token_expired(st.session_state.token_info):
        st.session_state.spotify_client = spotipy.Spotify(auth=st.session_state.token_info['access_token'])

# --- OAuth Callback (URL'den 'code' alma) Mantığı ---
# Bu kısım sayfa her yüklendiğinde (form gönderilmeden de) çalışacak
try:
    auth_code = st.query_params.get("code")
except AttributeError: 
    query_params_experimental = st.experimental_get_query_params() # Eski Streamlit versiyonları için fallback
    auth_code = query_params_experimental.get("code", [None])[0]

if auth_code:
    # Eğer URL'de 'code' varsa ve henüz geçerli bir token'ımız yoksa (veya emin değilsek)
    # Bu blok sadece bir kez çalışmalı (code işlendikten sonra)
    if not st.session_state.get('auth_code_processed_flag', False) or not st.session_state.token_info:
        st.session_state.auth_code_processed_flag = True # Bu kodu işlediğimizi işaretle
        # st.write(f"DEBUG: URL'de yetkilendirme kodu bulundu: {auth_code[:30]}...") 
        try:
            token_info = sp_oauth.get_access_token(auth_code, check_cache=False) # Kodu kullanarak token al
            st.session_state.token_info = token_info
            st.session_state.spotify_client = spotipy.Spotify(auth=token_info['access_token'])
            # st.write("DEBUG: Token başarıyla alındı ve session_state'e kaydedildi.")
            try: # URL'den kodu temizle
                st.query_params.clear() 
            except AttributeError:
                st.experimental_set_query_params()
            st.success("Spotify kimlik doğrulaması başarılı!")
            st.info("Harika! Artık playlist oluşturma formunu kullanabilirsiniz.")
            st.rerun() # Sayfayı temiz bir şekilde yeniden yükle ve doğru arayüzü göster
        except Exception as e:
            st.error(f"Spotify token alınırken hata: {e}")
            st.exception(e)
            st.session_state.token_info = None
            st.session_state.spotify_client = None
            st.session_state.auth_code_processed_flag = False # Hata olursa flag'i sıfırla
# --- OAuth Callback Sonu ---


# --- Arayüzün Ana Mantığı: Giriş Yapılmış mı, Yapılmamış mı? ---
if st.session_state.spotify_client and st.session_state.token_info and not sp_oauth.is_token_expired(st.session_state.token_info):
    # --- KULLANICI GİRİŞ YAPMIŞ: Playlist Oluşturma Formunu Göster ---
    try:
        user_info = st.session_state.spotify_client.me()
        st.success(f"Hoş geldin, {user_info.get('display_name', 'kullanıcı')}! Spotify'a bağlısın.")
    except Exception as e:
        # Token süresi dolmuş veya geçersiz olmuş olabilir, tekrar login olmasını isteyelim
        st.warning("Spotify bağlantınızda bir sorun var gibi görünüyor. Lütfen tekrar bağlanın.")
        st.session_state.token_info = None
        st.session_state.spotify_client = None
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f"Lütfen Spotify'a tekrar bağlanmak için **[bu linke tıklayın]({auth_url})**.", unsafe_allow_html=True)
        st.stop() # Formu gösterme

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
            sp = st.session_state.spotify_client # Zaten doğrulanmış client'ı kullan
            with st.spinner("Şarkılar aranıyor ve playlist oluşturuluyor... Lütfen bekleyin... ⏳"):
                tracks_found = spotify_sarki_ara_ve_goster(sp, muzik_turu, int(sarki_sayisi_st), istege_bagli_sanatci_st)
                if tracks_found:
                    create_spotify_playlist_with_tracks(sp, tracks_found, yeni_playlist_adi)
    
    # Oturumu kapatma butonu (opsiyonel)
    if st.button("Spotify Bağlantısını Kes"):
        st.session_state.token_info = None
        st.session_state.spotify_client = None
        st.session_state.auth_code_processed_flag = False # Bunu da sıfırla
        try: # URL'den ?code varsa temizle
            st.query_params.clear()
        except AttributeError:
            st.experimental_set_query_params()
        st.rerun()

else:
    # --- KULLANICI GİRİŞ YAPMAMIŞ: Giriş Linkini Göster ---
    st.warning("Uygulamayı kullanmak için lütfen Spotify hesabınızla bağlanın.")
    try:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f"Lütfen Spotify'a bağlanmak ve uygulamaya izin vermek için **[bu linke tıklayın]({auth_url})**.", unsafe_allow_html=True)
        st.info("İzin verdikten sonra Spotify sizi bu uygulamaya geri yönlendirecektir. Sayfa otomatik olarak güncellenip kullanılabilir hale gelecektir.")
    except Exception as e:
        st.error(f"Spotify yetkilendirme linki oluşturulurken bir sorun oluştu: {e}")
        st.exception(e)

# --- Sidebar (Değişiklik yok) ---
st.sidebar.header("Nasıl Kullanılır?")
st.sidebar.info(
    "1. Eğer istenirse, 'Spotify'a Bağlan' linkine tıklayarak giriş yapın ve izin verin.\n"
    "2. Gerekli alanları doldurun (müzik türü, şarkı sayısı, playlist adı vb.).\n"
    "3. 'Şarkıları Bul ve Spotify Playlisti Oluştur' butonuna tıklayın.\n"
    "4. Playlistiniz Spotify hesabınızda oluşturulacak ve linki burada gösterilecektir."
)
st.sidebar.markdown("---")
st.sidebar.caption(f"© {2025} Playlist Oluşturucu")
