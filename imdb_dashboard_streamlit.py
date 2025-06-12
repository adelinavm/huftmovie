import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

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
st.subheader("🤖 Rekomendasi Film Berdasarkan Mood")

mood_map = {
    "Petualangan": ["Adventure", "Action"],
    "Cinta": ["Romance", "Drama"],
    "Tegang": ["Thriller", "Crime", "Mystery"],
    "Lucu": ["Comedy"]
}

mood = st.selectbox("Pilih Mood Kamu", list(mood_map.keys()))
target_genres = mood_map[mood]

recommend = exploded[exploded['genres'].isin(target_genres)]
recommend = recommend.sort_values(by="rating", ascending=False).drop_duplicates("title")

st.markdown(f"Top rekomendasi untuk mood **{mood}**:")
st.table(recommend[['title', 'year', 'genres', 'rating']].head(10))

#Trending Movies This Year
st.subheader("🔥 Film Trending Tahun Ini")

latest_year = df['year'].max()
top_year = df[df['year'] == latest_year]
top_year = top_year.sort_values(by='numVotes', ascending=False)

st.markdown(f"Film dengan suara terbanyak di tahun **{latest_year}**:")
st.table(top_year[['title', 'year', 'rating', 'numVotes']].head(10))

# Footer
st.markdown("---")
st.caption("Built with ❤️ by 1 Adik 4 Kakak")
