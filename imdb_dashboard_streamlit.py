import streamlit as st
import pandas as pd
import plotly.express as px
from auth_utils import register_user, authenticate_user

st.set_page_config(layout="wide")

# --- Auth Section ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''

def show_login():
    st.title("🎬 IMDb Movie Dashboard - 1 Adik 4 Kakak")
    st.header("Sign In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        if authenticate_user(username, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success(f"Selamat datang, {username}!")
            st.rerun()
        else:
            st.error("Username atau password salah.")
    st.markdown("Belum punya akun?")
    if st.button("Register"):
        st.session_state['show_register'] = True
        st.rerun()

def show_register():
    st.title("🎬 IMDb Movie Dashboard - 1 Adik 4 Kakak")
    st.header("Register Akun Baru")
    username = st.text_input("Username Baru")
    password = st.text_input("Password Baru", type="password")
    password2 = st.text_input("Konfirmasi Password", type="password")
    if st.button("Register Akun"):
        if not username or not password:
            st.warning("Username dan password wajib diisi.")
        elif password != password2:
            st.warning("Password tidak cocok.")
        else:
            ok, msg = register_user(username, password)
            if ok:
                st.success(msg)
                st.session_state['show_register'] = False
                st.rerun()
            else:
                st.error(msg)
    if st.button("Kembali ke Login"):
        st.session_state['show_register'] = False
        st.rerun()

if 'show_register' not in st.session_state:
    st.session_state['show_register'] = False

if not st.session_state['logged_in']:
    if st.session_state['show_register']:
        show_register()
    else:
        show_login()
    st.stop()

# Load and clean data
@st.cache_data
def load_data():
    df = pd.read_csv("film_detail_complete_fixed.csv")
    df = df.dropna(subset=['title', 'genres', 'rating'])  # Hapus baris kosong
    df = df[df['title'] != "N/A"]
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')  # Pastikan rating numerik
    df = df.dropna(subset=['rating'])  # Hapus rating yang gagal dikonversi
    df['rating'] = df['rating'].astype(float)
    return df

df = load_data()

st.title("🎬 IMDb Movie Dashboard - 1 Adik 4 Kakak")

# Sidebar - Filters
st.sidebar.header("🔎 Filter Film")

# Tahun rilis
min_year = int(df['year'].min())
max_year = int(df['year'].max())
year_range = st.sidebar.slider("Tahun Rilis", min_year, 2025, (2000, 2025))

# Rating minimal
rating_min = st.sidebar.slider("Minimum Rating", 0.0, 10.0, 7.0, 0.1)

# Genre & Judul input
all_genres = sorted(set(g for sublist in df['genres'].str.split(', ') for g in sublist))
genre_input = st.sidebar.selectbox("Pilih Genre", ["Semua Genre"] + all_genres)
title_input = st.sidebar.text_input("Cari Judul Film", "").strip().lower()

# Filter data
filtered = df[
    (df['year'].between(year_range[0], year_range[1])) &
    (df['rating'] >= rating_min)
]

if genre_input != "Semua Genre":
    filtered = filtered[filtered['genres'].str.contains(genre_input, case=False)]

if title_input:
    filtered = filtered[filtered['title'].str.lower().str.contains(title_input)]

st.subheader("📄 Film Sesuai Filter")
filtered = filtered[filtered['title'].str.lower().str.contains(title_input, regex=False)]
if filtered.empty:
    st.warning("Tidak ada data yang sesuai dengan filter yang dipilih.")
else:
    st.dataframe(filtered[['title', 'year', 'genres', 'rating', 'numVotes']], use_container_width=True)

# Genre vs Rating Heatmap
st.subheader("📊 Rata-Rata Rating per Genre")
exploded = df.copy()
exploded['genres'] = exploded['genres'].str.split(", ")
exploded = exploded.explode('genres')
genre_rating = exploded.groupby('genres')['rating'].mean().sort_values(ascending=False).reset_index()
if exploded.empty or genre_rating.empty:
    st.warning("Data tidak tersedia untuk visualisasi genre.")
else:
    fig = px.bar(
        genre_rating,
        x='rating',
        y='genres',
        orientation='h',
        color='rating',
        color_continuous_scale='viridis',
        hover_data={'genres': True, 'rating': ':.2f'},
        labels={'rating': 'Rata-Rata Rating', 'genres': 'Genre'},
        title='Rata-Rata Rating per Genre'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

# --- Histori Pencarian Judul ---
if 'search_history' not in st.session_state:
    st.session_state['search_history'] = []

if title_input:
    # Simpan histori pencarian judul (maksimal 10 histori terakhir, tidak duplikat)
    if title_input not in st.session_state['search_history']:
        st.session_state['search_history'].insert(0, title_input)
        st.session_state['search_history'] = st.session_state['search_history'][:10]

# --- Section Baru: Rekomendasi Berdasarkan Histori Pencarian Judul ---
st.markdown('---')
st.subheader("🔎 Rekomendasi Berdasarkan Histori Pencarian Judul")
if st.session_state['search_history']:
    st.markdown("Histori pencarian judul: " + ", ".join(st.session_state['search_history']))
    # Gabungkan semua judul dari histori, cari film yang judulnya mengandung salah satu histori
    history_pattern = '|'.join([h for h in st.session_state['search_history'] if h])
    if history_pattern:
        history_recommend = df[df['title'].str.lower().str.contains(history_pattern, regex=True)]
        if not history_recommend.empty:
            st.table(history_recommend[['title', 'year', 'genres', 'rating']].drop_duplicates('title').head(10))
        else:
            st.info("Tidak ada rekomendasi dari histori pencarian.")
else:
    st.info("Belum ada histori pencarian judul.")

# Mood-based Recommendation
st.subheader("🤖 Rekomendasi Film Berdasarkan Mood & Genre")

# Update mood options
mood_map = {
    "Bersemangat": ["Adventure", "Action"],
    "Jatuh Cinta": ["Romance", "Drama"],
    "Berani": ["Thriller", "Crime", "Mystery"],
    "Sedih": ["Drama", "Romance"],
    "Happy": ["Comedy", "Family", "Animation"],
    "Badmood": ["Comedy", "Adventure", "Fantasy"]
}

mood = st.selectbox("Pilih Mood Kamu", list(mood_map.keys()))
user_genre = st.selectbox("(Opsional) Tambah Genre Favoritmu", ["-"] + all_genres)
target_genres = mood_map[mood].copy()
if user_genre != "-":
    target_genres.append(user_genre)

recommend = exploded[exploded['genres'].isin(target_genres)]
recommend = recommend.sort_values(by="rating", ascending=False).drop_duplicates("title")

st.markdown(f"Top rekomendasi untuk mood **{mood}**{f' & genre **{user_genre}**' if user_genre != '-' else ''}:")
recommend['year'] = recommend['year'].astype(int)
st.table(recommend[['title', 'year', 'genres', 'rating']].head(10))

# Trending Movies This Year
st.subheader("🔥 Film Trending Tahun Ini")

latest_year = df['year'].max()
top_year = df[df['year'] == latest_year]
top_year = top_year.sort_values(by='numVotes', ascending=False)

fig_trend = px.bar(
    top_year.head(10),
    x='title',
    y='numVotes',
    color='rating',
    hover_data=['title', 'rating', 'numVotes'],
    labels={'title': 'Judul Film', 'numVotes': 'Jumlah Suara', 'rating': 'Rating'},
    title=f'Film dengan suara terbanyak di tahun {int(latest_year)}'
)
fig_trend.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_trend, use_container_width=True)

# Visualisasi tren film sekarang (jumlah film per genre per tahun)
st.subheader("📈 Tren Film Saat Ini")

trend_data = exploded[exploded['year'] >= latest_year - 5]  # 5 tahun terakhir
trend = trend_data.groupby(['year', 'genres']).size().reset_index(name='count')

# Dropdown untuk memilih genre
all_genres = sorted(trend['genres'].unique())
selected_genre = st.selectbox("Pilih Genre", ["Semua Genre"] + all_genres)

if selected_genre != "Semua Genre":
    trend_filtered = trend[trend['genres'] == selected_genre]
else:
    trend_filtered = trend

fig2 = px.line(
    trend_filtered,
    x='year',
    y='count',
    color='genres',
    markers=True,
    hover_data=['genres', 'count'],
    labels={'count': 'Jumlah Film', 'year': 'Tahun', 'genres': 'Genre'},
    title='Jumlah Film per Genre (5 Tahun Terakhir)'
)
st.plotly_chart(fig2, use_container_width=True)

# Top 10 Film Terlaris berdasarkan genre yang dipilih
if selected_genre != "Semua Genre":
    st.subheader(f"🏆 Top 10 Film Terlaris dalam Genre '{selected_genre}'")
    top_genre = exploded[exploded['genres'] == selected_genre]
    top_genre = top_genre.sort_values(by='numVotes', ascending=False).drop_duplicates('title')
    top_genre['year'] = top_genre['year'].astype(int)
    st.table(top_genre[['title', 'year', 'rating', 'numVotes']].head(10))

# Footer
st.markdown("---")
st.caption("Built with ❤️ by 1 Adik 4 Kakak")
