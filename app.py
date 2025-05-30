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
def get_spotify_oauth():
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        print("HATA: API Kimlik bilgileri (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) Secrets'da eksik veya okunamadı!")
        return None 
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI, 
        scope=SCOPE
    )

# --- Playlist Oluşturma Fonksiyonu ---
def create_spotify_playlist_with_tracks(sp, tracks_to_add, playlist_name, public=True, description="Streamlit ile oluşturuldu"):
    if not tracks_to_add:
        st.warning("Playliste eklenecek şarkı bulunamadı.")
        return None
    try:
        # st.write("DEBUG: Playlist oluşturma fonksiyonu başladı.")
        user_id = sp.me()["id"] 
        # st.write(f"DEBUG: Kullanıcı ID'si alındı: {user_id}")
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=public, description=description)
        playlist_id = playlist["id"]
        playlist_url = playlist["external_urls"]["spotify"]
        # st.write(f"DEBUG: Playlist oluşturuldu. ID: {playlist_id}")
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

# --- Ana Arama ve Listeleme Fonksiyonu ---
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

    # st.write("DEBUG: spotify_sarki_ara_ve_goster fonksiyonu başladı.")
    try:
        # st.write(f"DEBUG: sp.search çağrısı yapılacak. Sorgu: {query}, Limit: {sarki_sayisi}")
        results = sp.search(q=query, type='track', limit=sarki_sayisi) 
        # st.write("DEBUG: sp.search çağrısı tamamlandı.")
        tracks = results.get('tracks', {}).get('items', [])
        # st.write(f"DEBUG: spotify_sarki_ara_ve_goster - Bulunan track sayısı: {len(tracks)}")

        if not tracks:
            st.warning("Belirttiğiniz kriterlere uygun şarkı Spotify'da bulunamadı.")
            return [] 

        st.subheader("🎶 Bulunan Şarkılar (Playlist'e Eklenmek Üzere): 🎶")
        for i, track_item in enumerate(tracks):
            # ... (şarkı gösterme kısmı aynı) ...
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

# --- Streamlit Arayüzü ---
st.set_page_config(page_title="Playlist Oluşturucu", page_icon="🎶", layout="centered")
st.title("🎶 Spotify Playlist Oluşturucu 🎶")
st.markdown("Sevdiğin türe ve sanatçıya göre şarkıları bul ve **otomatik olarak Spotify playlisti oluştur!**")

# API Anahtarları kontrolü
if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    st.error("Spotify API anahtarları (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) Streamlit Secrets'da ayarlanmamış veya okunamadı! Lütfen uygulamanın Streamlit Cloud ayarlarından kontrol edin.")
    st.stop()

try:
    sp_oauth = get_spotify_oauth() 
    if sp_oauth is None: 
        st.error("Spotify OAuth ayarları başlatılamadı. API anahtarları (Secrets) doğru girildi mi?")
        st.stop()
except Exception as e_oauth_init:
    st.error(f"Spotify OAuth başlatılırken kritik hata: {e_oauth_init}")
    st.exception(e_oauth_init)
    st.stop()

# Session state'de token bilgisini ve spotify client nesnesini saklayalım
if 'token_info' not in st.session_state:
    st.session_state.token_info = None
if 'spotify_client' not in st.session_state: # Bu zaten vardı, kalsın
    st.session_state.spotify_client = None


# --- YENİ: URL'den auth code'u alma ve token oluşturma ---
# Bu kısım sayfa her yüklendiğinde (form gönderilmeden de) çalışacak
# st.experimental_get_query_params() yerine st.query_params kullandık
# st.experimental_set_query_params() yerine st.query_params.clear() kullandık
# st.experimental_rerun() yerine st.rerun() kullandık (Streamlit 1.29.0+ versiyonunda)
# Eğer Streamlit versiyonun daha eskiyse st.experimental_rerun() kalsın. Şimdilik st.rerun() varsayıyorum.

# URL'den 'code' parametresini al
try:
    # query_params = st.experimental_get_query_params() # Eski versiyon
    query_params = st.query_params # Yeni versiyon
    auth_code = query_params.get("code") # .get("code") direkt string veya None döner. Listeye gerek yok.
except AttributeError: # st.query_params daha eski Streamlit versiyonlarında olmayabilir
    query_params = st.experimental_get_query_params()
    auth_code = query_params.get("code", [None])[0]


if auth_code and not st.session_state.token_info: # Eğer URL'de kod varsa VE session'da token yoksa
    st.write(f"DEBUG: URL'de yetkilendirme kodu bulundu: {auth_code[:30]}...") 
    try:
        token_info = sp_oauth.get_access_token(auth_code, check_cache=False)
        st.session_state.token_info = token_info
        st.session_state.spotify_client = spotipy.Spotify(auth=token_info['access_token'])
        st.write("DEBUG: Token başarıyla alındı ve session_state'e kaydedildi.")
        
        # URL'den kodu temizle ve sayfayı yeniden yükle
        # st.experimental_set_query_params() # Eski versiyon
        st.query_params.clear() # Yeni versiyon
        st.success("Spotify kimlik doğrulaması başarılı! Şimdi formu doldurup playlist oluşturabilirsiniz.")
        
        # st.experimental_rerun() # Eski versiyon
        # st.rerun() # Yeni versiyon (Streamlit 1.29.0+) 
        # rerun() hemen ardından st.stop() gerektirmez, scripti baştan çalıştırır.
        # rerun yerine sadece success mesajı gösterip kullanıcıdan butona tekrar basmasını da isteyebiliriz.
        # Şimdilik rerun'ı yorum satırı yapalım, kullanıcı butona tekrar bassın.
        st.info("Lütfen şimdi formu doldurup 'Playlist Oluştur' butonuna tekrar basın.")

    except Exception as e:
        st.error(f"Spotify token alınırken hata: {e}")
        st.exception(e)
        st.session_state.token_info = None
        st.session_state.spotify_client = None
# --- URL'den code alma sonu ---


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
        
        # Token'ın session_state'de olup olmadığını ve geçerli olup olmadığını kontrol et
        token_info_in_session = st.session_state.get('token_info')
        
        st.write(f"DEBUG (form submit): st.session_state.token_info var mı? {'Evet' if token_info_in_session else 'Hayır'}")
        if token_info_in_session:
            st.write(f"DEBUG (form submit): token_info['expires_at'] = {token_info_in_session.get('expires_at')}")
            is_expired = sp_oauth.is_token_expired(token_info_in_session)
            st.write(f"DEBUG (form submit): sp_oauth.is_token_expired = {is_expired}")
        else:
            is_expired = True # Token yoksa, süresi dolmuş gibi davran

        if token_info_in_session and not is_expired:
            st.write("DEBUG: Geçerli token session_state'de bulundu. Spotify client oluşturuluyor.")
            # sp = st.session_state.spotify_client # Bu zaten token alındığında set edilmiş olmalı
            sp = spotipy.Spotify(auth=token_info_in_session['access_token']) # Her zaman güncel token ile oluştur
            
            try:
                user_info_check = sp.me() # Bağlantıyı teyit et
                st.success(f"Spotify'a '{user_info_check.get('display_name', 'bilinmeyen kullanıcı')}' olarak bağlısınız.")
                st.write("DEBUG: Şarkı arama ve playlist oluşturmaya geçiliyor.")
                with st.spinner("Şarkılar aranıyor ve playlist oluşturuluyor... Lütfen bekleyin... ⏳"):
                    tracks_found = spotify_sarki_ara_ve_goster(sp, muzik_turu, int(sarki_sayisi_st), istege_bagli_sanatci_st)
                    if tracks_found:
                        create_spotify_playlist_with_tracks(sp, tracks_found, yeni_playlist_adi)
            except Exception as e:
                st.error(f"Spotify işlemi sırasında hata: {e}")
                st.exception(e)
                st.session_state.token_info = None # Sorun varsa token'ı temizle, tekrar login denesin
                st.session_state.spotify_client = None
                st.warning("Spotify bağlantısında bir sorun oluştu. Lütfen sayfayı yenileyip tekrar giriş yapmayı deneyin veya aşağıdaki linki kullanın.")
                try:
                    auth_url = sp_oauth.get_authorize_url()
                    st.markdown(f"Lütfen Spotify'a giriş yapmak
