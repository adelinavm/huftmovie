import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
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
genre_input = st.sidebar.text_input("Cari Genre", "Drama").strip().lower()
title_input = st.sidebar.text_input("Cari Judul Film", "").strip().lower()

# Filter data
filtered = df[
    (df['year'].between(year_range[0], year_range[1])) &
    (df['rating'] >= rating_min)
]

if genre_input:
    filtered = filtered[filtered['genres'].str.lower().str.contains(genre_input)]

if title_input:
    filtered = filtered[filtered['title'].str.lower().str.contains(title_input)]

st.subheader("📄 Film Sesuai Filter")
st.dataframe(filtered[['title', 'year', 'genres', 'rating', 'numVotes']], use_container_width=True)

# Genre vs Rating Heatmap
st.subheader("📊 Rata-Rata Rating per Genre")

exploded = df.copy()
exploded['genres'] = exploded['genres'].str.split(", ")
exploded = exploded.explode('genres')

genre_rating = exploded.groupby('genres')['rating'].mean().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(x=genre_rating.values, y=genre_rating.index, palette="viridis", ax=ax)
ax.set_xlabel("Rata-Rata Rating")
ax.set_ylabel("Genre")
ax.set_title("Rata-Rata Rating per Genre")
st.pyplot(fig)

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
user_genre = st.text_input("(Opsional) Tambah Genre Favoritmu", "").strip().title()
target_genres = mood_map[mood].copy()
if user_genre:
    target_genres.append(user_genre)

recommend = exploded[exploded['genres'].isin(target_genres)]
recommend = recommend.sort_values(by="rating", ascending=False).drop_duplicates("title")

st.markdown(f"Top rekomendasi untuk mood **{mood}**{f' & genre **{user_genre}**' if user_genre else ''}:")
recommend['year'] = recommend['year'].astype(int)
st.table(recommend[['title', 'year', 'genres', 'rating']].head(10))

# Trending Movies This Year
st.subheader("🔥 Film Trending Tahun Ini")

latest_year = df['year'].max()
top_year = df[df['year'] == latest_year]
top_year = top_year.sort_values(by='numVotes', ascending=False)

st.markdown(f"Film dengan suara terbanyak di tahun **{latest_year}**:")
top_year['year'] = top_year['year'].astype(int)
st.table(top_year[['title', 'year', 'rating', 'numVotes']].head(10))

# Visualisasi tren film sekarang (jumlah film per genre per tahun)
st.subheader("📈 Tren Film Saat Ini")
trend_data = exploded[exploded['year'] >= latest_year - 5]  # 5 tahun terakhir
trend = trend_data.groupby(['year', 'genres']).size().reset_index(name='count')
trend_pivot = trend.pivot(index='year', columns='genres', values='count').fillna(0)

fig2, ax2 = plt.subplots(figsize=(12, 6))
trend_pivot.plot(kind='bar', stacked=True, ax=ax2, colormap='tab20')
ax2.set_ylabel('Jumlah Film')
ax2.set_xlabel('Tahun')
ax2.set_title('Jumlah Film per Genre (5 Tahun Terakhir)')
ax2.legend(loc='upper left', bbox_to_anchor=(1, 1))
st.pyplot(fig2)

# Footer
st.markdown("---")
st.caption("Built with ❤️ by 1 Adik 4 Kakak")
