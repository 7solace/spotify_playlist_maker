import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- Spotify API Kimlik Bilgileri ve Ayarları ---
CLIENT_ID = st.secrets.get("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = st.secrets.get("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8501") 
    
SCOPE = "playlist-modify-public playlist-modify-private"

# --- Spotify Kimlik Doğrulama Fonksiyonu ---
def get_spotify_oauth():
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        print("HATA: API Kimlik bilgileri (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) Secrets'da eksik veya okunamadı!")
        # Bu fonksiyon arka planda çağrıldığı için st.error burada doğrudan görünmeyebilir.
        # Ana mantıkta bu kontrol zaten var.
        return None 
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )

# --- Playlist Oluşturma Fonksiyonu (DEBUG MESAJLARI EKLENDİ) ---
def create_spotify_playlist_with_tracks(sp, tracks_to_add, playlist_name, public=True, description="Streamlit ile oluşturuldu"):
    if not tracks_to_add:
        st.warning("Playliste eklenecek şarkı bulunamadı.")
        return None
    try:
        st.write("DEBUG: Playlist oluşturma fonksiyonu başladı.")
        st.write("DEBUG: Kullanıcı ID'si alınacak...")
        user_id = sp.me()["id"] 
        st.write(f"DEBUG: Kullanıcı ID'si alındı: {user_id}")
        
        st.write(f"DEBUG: '{playlist_name}' adında playlist oluşturulacak...")
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=public,
            description=description
        )
        playlist_id = playlist["id"]
        playlist_url = playlist["external_urls"]["spotify"]
        st.write(f"DEBUG: Playlist oluşturuldu. ID: {playlist_id}, URL: {playlist_url}")

        track_uris = [track["uri"] for track in tracks_to_add if track.get("uri")]
        if not track_uris:
            st.warning("Eklenecek geçerli şarkı URI'si bulunamadı.")
            return playlist_url 
        
        st.write(f"DEBUG: {len(track_uris)} şarkı playliste eklenecek: {playlist_id}")
        sp.playlist_add_items(playlist_id, track_uris)
        st.write("DEBUG: Şarkılar playliste eklendi.")
        
        st.success(f"'{playlist_name}' adında playlist başarıyla oluşturuldu!")
        st.markdown(f"**[Oluşturulan Playlisti Spotify'da Aç]({playlist_url})**")
        return playlist_url
    except Exception as e:
        st.write(f"DEBUG: create_spotify_playlist_with_tracks içinde hata: {str(e)}")
        st.error(f"Spotify playlisti oluşturulurken veya şarkılar eklenirken hata: {e}")
        st.exception(e) # Hatanın detayını arayüze yazdırır
        return None

# --- Ana Arama ve Listeleme Fonksiyonu (DEBUG MESAJLARI EKLENDİ) ---
def spotify_sarki_ara_ve_goster(sp, muzik_turu, sarki_sayisi, sanatci_adi_str):
    info_mesaji = f"Spotify'da"
    # ... (info_mesaji oluşturma kısmı aynı, önceki koddan kopyalayabilirsin) ...
    if muzik_turu:
        info_mesaji += f" '{muzik_turu.capitalize()}' türünde"
    if sanatci_adi_str:
        sanatci_temiz = sanatci_adi_str.strip()
        if muzik_turu and sanatci_temiz: info_mesaji += ","
        if sanatci_temiz: info_mesaji += f" sanatçı: {sanatci_temiz.title()} için" 
    else: 
        info_mesaji += "" 
    info_mesaji += f" {sarki_sayisi} şarkı aranıyor..."
    st.info(info_mesaji) # Bu kalsın
    
    query_parts = []
    # ... (query_parts oluşturma kısmı aynı) ...
    if muzik_turu:
        query_parts.append(f"genre:\"{muzik_turu.strip()}\"")
    if sanatci_adi_str:
        query_parts.append(f"artist:\"{sanatci_adi_str.strip()}\"")
    if not query_parts:
        st.warning("Arama yapmak için lütfen en az bir müzik türü veya sanatçı adı girin.")
        return []
    query = " ".join(query_parts)
    st.info(f"Gönderilen sorgu: {query}") # Bu da kalsın

    st.write("DEBUG: spotify_sarki_ara_ve_goster fonksiyonu başladı.")
    try:
        st.write(f"DEBUG: sp.search çağrısı yapılacak. Sorgu: {query}, Limit: {sarki_sayisi}")
        results = sp.search(q=query, type='track', limit=sarki_sayisi) 
        st.write("DEBUG: sp.search çağrısı tamamlandı.")
        
        if results and results['tracks'] and results['tracks']['items'] is not None:
            tracks = results['tracks']['items']
            st.write(f"DEBUG: Bulunan track sayısı: {len(tracks)}")
        else:
            st.write("DEBUG: sp.search'ten beklenen formatta sonuç gelmedi veya 'items' boş.")
            tracks = []

        if not tracks:
            st.warning("Belirttiğiniz kriterlere uygun şarkı Spotify'da bulunamadı.")
            return [] 

        st.subheader("🎶 Bulunan Şarkılar (Playlist'e Eklenmek Üzere): 🎶")
        # ... (Şarkıları gösterme döngüsü aynı, içine debug mesajı eklemeye gerek yok şimdilik) ...
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
        st.write("DEBUG: spotify_sarki_ara_ve_goster fonksiyonu sonlanıyor, şarkılar döndürülüyor.")
        return tracks 
    except Exception as e:
        st.write(f"DEBUG: spotify_sarki_ara_ve_goster içinde hata: {str(e)}")
        st.error(f"Spotify'dan şarkı ararken bir hata oluştu: {e}")
        st.exception(e) 
        return []

# --- Streamlit Arayüzü (Ana mantık) ---
st.set_page_config(page_title="Playlist Oluşturucu", page_icon="🎶", layout="centered")
st.title("🎶 Spotify Playlist Oluşturucu 🎶")
st.markdown("Sevdiğin türe ve sanatçıya göre şarkıları bul ve **otomatik olarak Spotify playlisti oluştur!**")

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    st.error("Spotify API anahtarları (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) Streamlit Secrets'da ayarlanmamış veya okunamadı! Lütfen uygulamanın Streamlit Cloud ayarlarından kontrol edin.")
    st.caption("Eğer bu mesajı yerelde görüyorsanız, kodun en başındaki CLIENT_ID, CLIENT_SECRET ve REDIRECT_URI değişkenlerine kendi bilgilerinizi girmeniz veya .streamlit/secrets.toml dosyası oluşturmanız gerekir.")
    st.stop()

sp_oauth = get_spotify_oauth() 
if sp_oauth is None: 
    st.error("Spotify OAuth ayarları başlatılamadı. API anahtarlarını kontrol edin (Secrets).")
    st.stop()

if 'spotify_client' not in st.session_state:
    st.session_state.spotify_client = None
if 'found_tracks' not in st.session_state:
    st.session_state.found_tracks = []

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
        st.write("DEBUG: Butona tıklandı, Spotify bağlantısı deneniyor...")
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        try:
            st.write("DEBUG: sp.me() çağrısı yapılacak (kimlik doğrulama testi)...")
            user_info = sp.me() 
            st.session_state.spotify_client = sp 
            st.success(f"Spotify'a '{user_info['display_name']}' olarak başarıyla bağlanıldı!")
            st.write("DEBUG: Spotify bağlantısı başarılı, şarkı arama ve playlist oluşturmaya geçiliyor.")
            
            with st.spinner("Şarkılar aranıyor ve playlist oluşturuluyor... Lütfen bekleyin... ⏳"):
                st.write("DEBUG: Spinner başlatıldı. spotify_sarki_ara_ve_goster çağrılacak.")
                st.session_state.found_tracks = spotify_sarki_ara_ve_goster(sp, muzik_turu, int(sarki_sayisi_st), istege_bagli_sanatci_st)
                st.write(f"DEBUG: spotify_sarki_ara_ve_goster döndü. Bulunan şarkı sayısı: {len(st.session_state.found_tracks if st.session_state.found_tracks else [])}")
                
                if st.session_state.found_tracks:
                    st.write("DEBUG: Şarkılar bulundu, create_spotify_playlist_with_tracks çağrılacak.")
                    create_spotify_playlist_with_tracks(sp, st.session_state.found_tracks, yeni_playlist_adi)
                    st.write("DEBUG: create_spotify_playlist_with_tracks tamamlandı.")
                else:
                    st.warning("Playlist oluşturmak için hiç şarkı bulunamadı.") # Bu mesaj zaten fonksiyonda da var.
        except Exception as auth_error:
            st.write(f"DEBUG: Ana try-except bloğunda hata: {str(auth_error)}")
            st.error(f"Spotify kimlik doğrulaması veya işlem sırasında bir sorun oluştu: {type(auth_error).__name__}")
            st.info(f"Lütfen sayfayı yenileyip tekrar deneyin. Sorun devam ederse, Spotify Geliştirici Panelindeki Yönlendirme URI'nizin ({REDIRECT_URI}) Streamlit Cloud Secrets'dakiyle aynı ve uygulamanızın genel adresi olduğundan emin olun.")
            st.exception(auth_error) # Hatanın detayını arayüze yazdırır
            st.session_state.spotify_client = None 

st.sidebar.header("Nasıl Kullanılır?")
# ... (sidebar kısmı aynı) ...
st.sidebar.info(
    "1. Gerekli alanları doldurun.\n"
    "2. 'Şarkıları Bul ve Spotify Playlisti Oluştur' butonuna tıklayın.\n"
    "3. Gerekirse Spotify kimlik doğrulama adımlarını (tarayıcı üzerinden) tamamlayın.\n"
    "4. Playlistiniz Spotify hesabınızda oluşturulacak ve linki burada gösterilecektir."
)
st.sidebar.markdown("---")
st.sidebar.caption(f"© {2025} Playlist Oluşturucu")
