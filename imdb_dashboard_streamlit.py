import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("film_detail_complete_fixed.csv")

df = load_data()

st.title("🎬 IMDb Movie Dashboard - 1 Adik 4 Kakak")

# Sidebar - Filters
st.sidebar.header("🔎 Filter Film")
years = st.sidebar.slider("Tahun Rilis", int(df['year'].min()), int(df['year'].max()), (2000, 2020))
rating_min = st.sidebar.slider("Minimum Rating", 0.0, 10.0, 7.0, 0.1)
genre_input = st.sidebar.text_input("Cari Genre", "Drama")
title_input = st.sidebar.text_input("Cari Judul Film", "")

# Filtered Data
filtered = df[
    (df['year'].between(years[0], years[1])) &
    (df['rating'] != "N/A") &
    (df['rating'].astype(float) >= rating_min) &
    (df['genres'].str.contains(genre_input, case=False)) &
    (df['title'].str.contains(title_input, case=False))
]

st.subheader("📄 Film Sesuai Filter")
st.dataframe(filtered[['title', 'year', 'genres', 'rating', 'numVotes']], use_container_width=True)

# Heatmap Genre vs Rating
st.subheader("📊 Rata-Rata Rating per Genre")
exploded = df.dropna(subset=['genres']).copy()
exploded['genres'] = exploded['genres'].str.split(", ")
exploded = exploded.explode("genres")
exploded = exploded[exploded['rating'] != "N/A"]
exploded['rating'] = exploded['rating'].astype(float)

heatmap_data = exploded.groupby('genres')['rating'].mean().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(x=heatmap_data.values, y=heatmap_data.index, palette="viridis", ax=ax)
ax.set_xlabel("Rata-Rata Rating")
ax.set_ylabel("Genre")
ax.set_title("Heatmap Genre vs Rating")
st.pyplot(fig)

# Rekomendasi berdasarkan Mood
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

# Film Trending Tahun Ini
st.subheader("🔥 Film Trending Tahun Ini")
top_year = df[df['year'] == df['year'].max()]
top_year = top_year[top_year['rating'] != "N/A"]
top_year['rating'] = top_year['rating'].astype(float)
st.table(top_year.sort_values(by='numVotes', ascending=False)[['title', 'year', 'rating', 'numVotes']].head(10))

st.markdown("---")
st.caption("Built with ❤️ by 1 Adik 4 Kakak")
