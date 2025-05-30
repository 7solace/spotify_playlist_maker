import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyOauthError

# --- Spotify API Kimlik Bilgileri ve Ayarları ---
CLIENT_ID = st.secrets.get("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = st.secrets.get("SPOTIPY_REDIRECT_URI") # Fallback'i kaldırdık, Secrets'da kesin olmalı
    
SCOPE = "playlist-modify-public playlist-modify-private"

# --- Spotify Kimlik Doğrulama Fonksiyonu ---
def get_spotify_oauth():
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        # Bu hata, aşağıdaki ana kontrol tarafından yakalanmalı.
        return None 
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI, 
        scope=SCOPE,
        # open_browser=True (varsayılan) - Tarayıcıyı açmaya çalışacak
        # cache_path=None # Streamlit Cloud'da dosya sistemi kalıcı olmayabilir, session_state daha iyi
    )

# --- Playlist Oluşturma Fonksiyonu (DEBUG mesajları eklendi) ---
def create_spotify_playlist_with_tracks(sp, tracks_to_add, playlist_name, public=True, description="Streamlit ile oluşturuldu"):
    if not tracks_to_add:
        st.warning("Playliste eklenecek şarkı bulunamadı.")
        return None
    try:
        # st.write("DEBUG: create_spotify_playlist_with_tracks fonksiyonu başladı.") # Tekrarlayan debug mesajlarını azalttım
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
        st.markdown(f"**[Oluşturulan Playlisti Spotify'da Aç]({playlist_url})**")
        return playlist_url
    except Exception as e:
        st.error(f"Spotify playlisti oluşturulurken veya şarkılar eklenirken hata: {e}")
        st.exception(e)
        return None

# --- Ana Arama ve Listeleme Fonksiyonu (DEBUG mesajları eklendi) ---
def spotify_sarki_ara_ve_goster(sp, muzik_turu, sarki_sayisi, sanatci_adi_str):
    # ... (info_mesaji ve query oluşturma kısmı aynı) ...
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

    st.write("DEBUG: spotify_sarki_ara_ve_goster - sp.search çağrısı yapılacak...")
    try:
        results = sp.search(q=query, type='track', limit=sarki_sayisi) 
        st.write("DEBUG: spotify_sarki_ara_ve_goster - sp.search çağrısı tamamlandı.")
        tracks = results.get('tracks', {}).get('items', [])
        st.write(f"DEBUG: spotify_sarki_ara_ve_goster - Bulunan track sayısı: {len(tracks)}")

        if not tracks:
            st.warning("Belirttiğiniz kriterlere uygun şarkı Spotify'da bulunamadı.")
            return [] 

        st.subheader("🎶 Bulunan Şarkılar (Playlist'e Eklenmek Üzere): 🎶")
        # ... (Şarkıları gösterme döngüsü aynı) ...
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
        st.write(f"DEBUG: spotify_sarki_ara_ve_goster içinde hata: {str(e)}")
        st.error(f"Spotify'dan şarkı ararken bir hata oluştu: {e}")
        st.exception(e) 
        return []

# --- Streamlit Arayüzü ---
st.set_page_config(page_title="Playlist Oluşturucu", page_icon="🎶", layout="centered")
st.title("🎶 Spotify Playlist Oluşturucu 🎶")
st.markdown("Sevdiğin türe göre şarkıları bul ve **otomatik olarak Spotify playlisti oluştur!**")

# API Anahtarları ve OAuth nesnesi en başta kontrol ediliyor
if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    st.error("Spotify API anahtarları (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) Streamlit Secrets'da ayarlanmamış veya okunamadı! Lütfen uygulamanın Streamlit Cloud ayarlarından kontrol edin.")
    st.stop()

sp_oauth = get_spotify_oauth()
if sp_oauth is None:
    st.error("Spotify OAuth ayarları başlatılamadı. API anahtarları (Secrets) doğru girildi mi?")
    st.stop()

# Token bilgisini session_state'de saklayalım
if 'token_info' not in st.session_state:
    st.session_state.token_info = None

# URL'den auth code'u al (Spotify yönlendirmesinden sonra)
query_params = st.experimental_get_query_params()
auth_code = query_params.get("code", [None])[0]

if auth_code and not st.session_state.token_info: # Eğer code varsa ve token daha alınmamışsa
    st.write(f"DEBUG: URL'de yetkilendirme kodu bulundu: {auth_code[:20]}...") # Kodu kısmen göster
    try:
        token_info = sp_oauth.get_access_token(auth_code, check_cache=False)
        st.session_state.token_info = token_info
        # Token alındıktan sonra URL'den kodu temizlemek için sayfayı yeniden yükle
        st.experimental_set_query_params() # Parametreleri temizler
        st.success("Spotify kimlik doğrulaması başarılı! Şimdi formu doldurup playlist oluşturabilirsiniz.")
        st.experimental_rerun() # Sayfayı temiz bir şekilde yeniden yükle
    except Exception as e:
        st.error(f"Spotify token alınırken hata: {e}")
        st.exception(e)
        st.session_state.token_info = None

# Ana Form
with st.form("playlist_form"):
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
        st.write("DEBUG: Butona tıklandı.")
        if st.session_state.token_info and not sp_oauth.is_token_expired(st.session_state.token_info):
            st.write("DEBUG: Geçerli token session_state'de bulundu.")
            sp = spotipy.Spotify(auth=st.session_state.token_info['access_token'])
            
            # Kullanıcı bilgisini alıp ekrana yazdıralım (opsiyonel ama bağlantıyı teyit eder)
            try:
                user_info_check = sp.me()
                st.success(f"Spotify'a '{user_info_check.get('display_name', 'bilinmeyen kullanıcı')}' olarak bağlısınız.")
                st.write("DEBUG: Şarkı arama ve playlist oluşturmaya geçiliyor.")
                with st.spinner("Şarkılar aranıyor ve playlist oluşturuluyor... Lütfen bekleyin... ⏳"):
                    tracks_found = spotify_sarki_ara_ve_goster(sp, muzik_turu, int(sarki_sayisi_st), istege_bagli_sanatci_st)
                    if tracks_found:
                        create_spotify_playlist_with_tracks(sp, tracks_found, yeni_playlist_adi)
            except Exception as e:
                st.error(f"Spotify işlemi sırasında hata: {e}")
                st.exception(e)
                # Token'da sorun olabilir, tekrar login olmasını isteyelim
                st.session_state.token_info = None # Token'ı temizle
                auth_url = sp_oauth.get_authorize_url()
                st.warning("Spotify bağlantısında bir sorun oluştu. Lütfen tekrar giriş yapın.")
                st.markdown(f"Lütfen Spotify'a giriş yapmak ve izin vermek için **[bu linke tıklayın]({auth_url})**.", unsafe_allow_html=True)
                st.info("İzin verdikten sonra bu sayfaya geri yönlendirileceksiniz. Sayfa güncellendikten sonra tekrar deneyin.")

        else: # Token yok veya süresi dolmuşsa
            st.write("DEBUG: Geçerli token yok, kullanıcı Spotify'a yönlendirilecek.")
            auth_url = sp_oauth.get_authorize_url()
            st.warning("Spotify ile kimlik doğrulamanız gerekiyor.")
            st.markdown(f"Lütfen Spotify'a giriş yapmak ve bu uygulamaya izin vermek için **[bu linke tıklayın]({auth_url})**.", unsafe_allow_html=True)
            st.info("İzin verdikten sonra Spotify sizi bu uygulamaya geri yönlendirecektir (`?code=` içeren bir adresle). O sayfaya geldiğinizde, **bu uygulamaya geri dönüp yukarıdaki 'Şarkıları Bul ve Spotify Playlisti Oluştur' butonuna tekrar tıklamanız** gerekebilir (veya sayfa otomatik olarak işlemi devam ettirebilir).")

st.sidebar.header("Nasıl Kullanılır?")
st.sidebar.info(
    "1. Gerekli alanları doldurun.\n"
    "2. 'Şarkıları Bul ve Spotify Playlisti Oluştur' butonuna tıklayın.\n"
    "3. **İlk kullanımda,** size gösterilen linke tıklayarak Spotify'a giriş yapın ve uygulamaya izin verin.\n"
    "4. Spotify sizi uygulamaya geri yönlendirdikten sonra, bazen işlemi tamamlamak için butona **tekrar** tıklamanız gerekebilir.\n"
    "5. Playlistiniz Spotify hesabınızda oluşturulacak ve linki burada gösterilecektir."
)
st.sidebar.markdown("---")
st.sidebar.caption(f"© {2025} Playlist Oluşturucu")
