import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyOauthError # Bu hatayı özel olarak yakalamak için ekledik

# --- Spotify API Kimlik Bilgileri ve Ayarları ---
# Bu bilgiler Streamlit Cloud'daki "Secrets" bölümünden okunacak.
CLIENT_ID = st.secrets.get("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("SPOTIPY_CLIENT_SECRET")
# Bu URI, Streamlit Cloud uygulaman yayınlandıktan sonra alacağı genel adrese göre
# Secrets bölümünde güncellenecek. Fallback değeri, yerelde veya Secrets henüz ayarlanmadığında kullanılır.
REDIRECT_URI = st.secrets.get("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8501") 
    
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
        # open_browser=True (varsayılan)
    )

# --- Playlist Oluşturma Fonksiyonu ---
def create_spotify_playlist_with_tracks(sp, tracks_to_add, playlist_name, public=True, description="Streamlit ile oluşturuldu"):
    if not tracks_to_add:
        st.warning("Playliste eklenecek şarkı bulunamadı.")
        return None
    try:
        st.write("DEBUG: Playlist oluşturma fonksiyonu başladı.")
        user_id = sp.me()["id"] 
        st.write(f"DEBUG: Kullanıcı ID'si alındı: {user_id}")
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=public, description=description)
        playlist_id = playlist["id"]
        playlist_url = playlist["external_urls"]["spotify"]
        st.write(f"DEBUG: Playlist oluşturuldu. ID: {playlist_id}")
        track_uris = [track["uri"] for track in tracks_to_add if track.get("uri")]
        if not track_uris:
            st.warning("Eklenecek geçerli şarkı URI'si bulunamadı.")
            return playlist_url 
        sp.playlist_add_items(playlist_id, track_uris)
        st.write("DEBUG: Şarkılar playliste eklendi.")
        st.success(f"'{playlist_name}' adında playlist başarıyla oluşturuldu!")
        st.markdown(f"**[Oluşturulan Playlisti Spotify'da Aç]({playlist_url})**")
        return playlist_url
    except Exception as e:
        st.write(f"DEBUG: create_spotify_playlist_with_tracks içinde hata: {str(e)}")
        st.error(f"Spotify playlisti oluşturulurken veya şarkılar eklenirken hata: {e}")
        st.exception(e)
        return None

# --- Ana Arama ve Listeleme Fonksiyonu ---
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
st.markdown("Sevdiğin türe ve sanatçıya göre şarkıları bul ve **otomatik olarak Spotify playlisti oluştur!**")

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    st.error("Spotify API anahtarları (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) Streamlit Secrets'da ayarlanmamış veya okunamadı! Lütfen uygulamanın Streamlit Cloud ayarlarından kontrol edin.")
    st.caption("Eğer bu mesajı yerelde görüyorsanız, kodun en başındaki CLIENT_ID, CLIENT_SECRET ve REDIRECT_URI değişkenlerine kendi bilgilerinizi girmeniz veya .streamlit/secrets.toml dosyası oluşturmanız gerekir.")
    st.stop()

try:
    sp_oauth = get_spotify_oauth() 
    if sp_oauth is None: 
        st.error("Spotify OAuth ayarları başlatılamadı. API anahtarları (Secrets) doğru girildi mi veya get_spotify_oauth içinde bir sorun mu var?")
        st.stop()
except Exception as e_oauth_init:
    st.error(f"Spotify OAuth başlatılırken kritik hata: {e_oauth_init}")
    st.exception(e_oauth_init)
    st.stop()

if 'token_info' not in st.session_state:
    st.session_state.token_info = None

# query_params = st.experimental_get_query_params() # Eski Streamlit versiyonu
# auth_code = query_params.get("code", [None])[0] # Eski Streamlit versiyonu
try:
    auth_code = st.query_params.get("code") # Yeni Streamlit versiyonu (string veya None döner)
except AttributeError: # Eğer st.query_params yoksa (eski Streamlit versiyonuysa)
    query_params_experimental = st.experimental_get_query_params()
    auth_code = query_params_experimental.get("code", [None])[0]


if auth_code and not st.session_state.get('token_obtained_this_run', False):
    st.write(f"DEBUG: URL'de yetkilendirme kodu bulundu: {auth_code[:30]}...") 
    try:
        token_info = sp_oauth.get_access_token(auth_code, check_cache=False)
        st.session_state.token_info = token_info
        st.session_state.spotify_client = spotipy.Spotify(auth=token_info['access_token'])
        st.session_state.token_obtained_this_run = True # Bu çalıştırmada token aldığımızı işaretle
        st.write("DEBUG: Token başarıyla alındı ve session_state'e kaydedildi.")
        
        # URL'den kodu temizle
        # st.experimental_set_query_params() # Eski Streamlit versiyonu
        try:
            st.query_params.clear() # Yeni Streamlit versiyonu
        except AttributeError:
            st.experimental_set_query_params() # Çok eski versiyonlar için fallback
            
        st.success("Spotify kimlik doğrulaması başarılı!")
        st.info("Harika! Şimdi formu doldurup 'Playlist Oluştur' butonuna tekrar basarak playlistinizi oluşturabilirsiniz.")
        # st.rerun() # Otomatik yeniden çalıştırma yerine kullanıcıya bilgi verip tekrar butona basmasını isteyelim
                
    except Exception as e:
        st.error(f"Spotify token alınırken hata: {e}")
        st.exception(e)
        st.session_state.token_info = None
        st.session_state.spotify_client = None

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
        
        token_info_in_session = st.session_state.get('token_info')
        is_expired = True # Varsayılan olarak token yok veya geçersiz
        if token_info_in_session:
            is_expired = sp_oauth.is_token_expired(token_info_in_session)
            st.write(f"DEBUG (form submit): Token var. Süresi dolmuş mu? {is_expired}")
        else:
            st.write("DEBUG (form submit): Session_state'de token bulunmuyor.")

        if token_info_in_session and not is_expired:
            st.write("DEBUG: Geçerli token bulundu. Spotify işlemleri başlatılıyor.")
            sp = spotipy.Spotify(auth=token_info_in_session['access_token'])
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
                st.session_state.token_info = None 
                st.session_state.spotify_client = None
                # Kullanıcıyı tekrar yetkilendirmeye yönlendirmek için link göster
                auth_url = sp_oauth.get_authorize_url()
                st.warning("Spotify bağlantısında bir sorun oluştu veya token süresi doldu. Lütfen tekrar yetkilendirme yapın.")
                st.markdown(f"Lütfen Spotify'a giriş yapmak ve izin vermek için **[bu linke tıklayın]({auth_url})**.", unsafe_allow_html=True)
        else: 
            st.write("DEBUG: Geçerli token yok veya süresi dolmuş. Kullanıcıya yetkilendirme linki gösterilecek.")
            try:
                auth_url = sp_oauth.get_authorize_url()
                st.warning("Spotify ile kimlik doğrulamanız gerekiyor.")
                st.markdown(f"Lütfen Spotify'a giriş yapmak ve bu uygulamaya izin vermek için **[bu linke tıklayın]({auth_url})**.", unsafe_allow_html=True)
                st.info("İzin verdikten sonra Spotify sizi bu uygulamaya geri yönlendirecektir (`?code=` içeren bir adresle). O sayfaya geldiğinizde, **bu uygulama sayfası otomatik olarak güncellenecek** ve sizden formu doldurup butona tekrar basmanızı isteyecektir.")
            except Exception as e_auth_url:
                st.error(f"Spotify yetkilendirme URL'si oluşturulurken hata: {e_auth_url}")
                st.exception(e_auth_url)

st.sidebar.header("Nasıl Kullanılır?")
st.sidebar.info(
    "1. Gerekli alanları doldurun.\n"
    "2. 'Şarkıları Bul ve Spotify Playlisti Oluştur' butonuna tıklayın.\n"
    "3. **İlk kullanımda,** size bir Spotify giriş linki gösterilebilir. O linke tıklayarak Spotify'a giriş yapın ve uygulamaya izin verin.\n"
    "4. İzin verdikten sonra Spotify sizi bu uygulamaya geri yönlendirecektir. Sayfa yenilendikten sonra (veya 'Spotify kimlik doğrulaması başarılı!' mesajını gördükten sonra) işlemi tamamlamak için formu doldurup butona **tekrar** tıklamanız gerekebilir.\n"
    "5. Playlistiniz Spotify hesabınızda oluşturulacak ve linki burada gösterilecektir."
)
st.sidebar.markdown("---")
st.sidebar.caption(f"© {2025} Playlist Oluşturucu")
