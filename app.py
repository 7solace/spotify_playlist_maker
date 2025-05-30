import streamlit as st
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- Spotify API Kimlik Bilgileri ve Ayarları ---
CLIENT_ID = "f6e59e8961504baf85d00ce67d084373" 
CLIENT_SECRET = "675c3457210148b8b9775c21f3b3f481" 
REDIRECT_URI = "http://127.0.0.1:8501" 
SCOPE = "playlist-modify-public playlist-modify-private"

# --- Yerel Şarkı Veritabanı (Yedek) ---
YEREL_SARKI_VERITABANI = [
    {"ad": "Bohemian Rhapsody", "sanatci": "Queen", "tur": "Rock", "album": "A Night at the Opera"},
    {"ad": "Sultan-ı Yegah", "sanatci": "Nur Yoldaş", "tur": "Anadolu Rock", "album": "Sultan-ı Yegah"},
]

# --- Spotify Kimlik Doğrulama Fonksiyonu ---
def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        open_browser=False,
    )

# --- Playlist Oluşturma Fonksiyonu (Değişiklik yok) ---
def create_spotify_playlist_with_tracks(sp, tracks_to_add, playlist_name, public=True, description="Streamlit ile oluşturuldu"):
    if not tracks_to_add:
        st.warning("Playliste eklenecek şarkı bulunamadı.")
        return None
    try:
        user_id = sp.me()["id"]
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=public,
            description=description
        )
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
        return None

# --- Ana Arama ve Listeleme Fonksiyonu (Bilgilendirme mesajı için küçük düzeltme) ---
def spotify_sarki_ara_ve_goster(sp, muzik_turu, sarki_sayisi, istege_bagli_sanatci_str):
    # Bilgilendirme mesajı için sanatçı listesini hazırla
    sanatci_listesi_display = []
    if istege_bagli_sanatci_str:
        sanatci_listesi_display = [s.strip() for s in istege_bagli_sanatci_str.split(',') if s.strip()]

    info_mesaji = f"Spotify'da"
    if muzik_turu:
        info_mesaji += f" '{muzik_turu.capitalize()}' türünde"
    if sanatci_listesi_display:
        artist_text_display = ", ".join(sanatci_listesi_display) # Kullanıcının girdiği gibi göster
        if muzik_turu: info_mesaji += ","
        info_mesaji += f" sanatçılar: {artist_text_display} arasından"
    info_mesaji += f" {sarki_sayisi} şarkı aranıyor..."
    st.info(info_mesaji)
    
    query_parts = []
    artist_query_segment_for_spotify = ""

    if istege_bagli_sanatci_str:
        sanatcilar_sorgu_icin = [s.strip() for s in istege_bagli_sanatci_str.split(',') if s.strip()]
        if sanatcilar_sorgu_icin:
            artist_query_segment_for_spotify = " OR ".join([f'artist:"{s}"' for s in sanatcilar_sorgu_icin])

    if muzik_turu:
        query_parts.append(f"genre:\"{muzik_turu}\"")
        if artist_query_segment_for_spotify:
            query_parts.append(f"({artist_query_segment_for_spotify})")
    elif artist_query_segment_for_spotify:
        query_parts.append(artist_query_segment_for_spotify)
        
    if not query_parts:
        st.warning("Arama yapmak için lütfen en az bir müzik türü veya sanatçı adı girin.")
        return []
        
    query = " ".join(query_parts)
    st.info(f"Gönderilen sorgu: {query}")

    try:
        results = sp.search(q=query, type='track', limit=sarki_sayisi) # market="TR" yok (global arama)
        tracks = results['tracks']['items']

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
                if len(album_images) > 1: 
                    album_art_url = album_images[1]['url'] 
                elif len(album_images) == 1:
                    album_art_url = album_images[0]['url'] 
            
            col_art, col_info = st.columns([1, 3]) 
            with col_art:
                if album_art_url:
                    st.image(album_art_url, width=100) 
                else:
                    st.caption("(Kapak yok)") 
            with col_info:
                st.markdown(f"**{i+1}. {sarki_adi}**")
                st.write(f"**Sanatçı(lar):** {sanatcilar_gosterim}")
                st.write(f"**Albüm:** {album_adi}")
                if spotify_url:
                    st.markdown(f"   [Şarkıyı Spotify'da Dinle]({spotify_url})")
            st.write("---") 
        return tracks 
    except Exception as e:
        st.error(f"Spotify'dan şarkı ararken bir hata oluştu: {e}")
        st.exception(e) 
        return []

# --- Streamlit Arayüzü (Değişiklik yok) ---
st.set_page_config(page_title="Playlist Oluşturucu Pro", page_icon="🎶", layout="centered")
st.title("🎶 Spotify Playlist Oluşturucu Pro 🎶")
st.markdown("Sevdiğin türe göre şarkıları bul ve **otomatik olarak Spotify playlisti oluştur!**")

sp_oauth = get_spotify_oauth() 

if 'spotify_client' not in st.session_state:
    st.session_state.spotify_client = None
if 'found_tracks' not in st.session_state:
    st.session_state.found_tracks = []

with st.form("playlist_form"):
    muzik_turu = st.text_input("Hangi türde şarkılar istersiniz?", placeholder="örn: Pop, Rock, Trap")
    sarki_sayisi_st = st.number_input("Kaç şarkı bulunsun ve playliste eklensin?", min_value=1, max_value=30, value=5)
    istege_bagli_sanatci_st = st.text_input("Belirli sanatçı(lar) var mı?", placeholder="örn: Tarkan (Birden fazlaysa virgülle ayırın: Tarkan, Sezen Aksu)")
    yeni_playlist_adi = st.text_input("Oluşturulacak Spotify Playlistinin Adı Ne Olsun?", f"{muzik_turu.capitalize() if muzik_turu else 'Yeni'} Streamlit Playlistim")
    
    submitted_search_and_create = st.form_submit_button("🎵 Şarkıları Bul ve Spotify Playlisti Oluştur")

if submitted_search_and_create:
    if not muzik_turu and not istege_bagli_sanatci_st: 
        st.warning("Lütfen bir müzik türü veya en az bir sanatçı adı girin.")
    elif not yeni_playlist_adi:
        st.warning("Lütfen oluşturulacak playlist için bir ad girin.")
    else:
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        try:
            user_info = sp.me() 
            st.session_state.spotify_client = sp 
            st.success(f"Spotify'a '{user_info['display_name']}' olarak başarıyla bağlanıldı!")
            
            with st.spinner("Şarkılar aranıyor ve playlist oluşturuluyor... Lütfen bekleyin... ⏳"):
                st.session_state.found_tracks = spotify_sarki_ara_ve_goster(sp, muzik_turu, int(sarki_sayisi_st), istege_bagli_sanatci_st)
                
                if st.session_state.found_tracks:
                    create_spotify_playlist_with_tracks(sp, st.session_state.found_tracks, yeni_playlist_adi)
                else:
                    st.warning("Playlist oluşturmak için hiç şarkı bulunamadı.")
        except Exception as auth_error:
            st.error(f"Spotify kimlik doğrulaması veya işlem sırasında hata: {auth_error}")
            st.info("Lütfen terminali kontrol edin. Spotify sizden bir linke gitmenizi veya bir URL yapıştırmanızı istiyor olabilir.")
            st.info("Gerekirse, tarayıcıda açılan Spotify ekranından izinleri verip, istenen URL'yi terminale yapıştırdıktan sonra butona tekrar tıklayın.")
            st.session_state.spotify_client = None 

st.sidebar.header("Nasıl Kullanılır?")
st.sidebar.info(
    "1. Gerekli alanları doldurun.\n"
    "   - Birden fazla sanatçı için isimleri **virgülle (,)** ayırın.\n"
    "2. 'Şarkıları Bul ve Spotify Playlisti Oluştur' butonuna tıklayın.\n"
    "3. Gerekirse Spotify kimlik doğrulama adımlarını (terminal ve tarayıcı üzerinden) tamamlayın.\n"
    "4. Playlistiniz Spotify hesabınızda oluşturulacak ve linki burada gösterilecektir."
)
st.sidebar.markdown("---")
st.sidebar.caption(f"© {2025} Playlist Oluşturucu Pro")