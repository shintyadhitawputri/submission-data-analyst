import pandas as pd
import matplotlib.pylot as plt
import seaborn as sns
import streamlit as st
import numpy as np
sns.set(style='dark')

#Helper Function
def create_weather_df(df):
    weather_df = df.groupby(by='weathersit').agg({
    'countrent': ['mean', 'sum']
})
    weather_df.columns = ['mean_rent', 'total_rent']
    sorted_weather_df = weather_df.sort_values(by='total_rent', ascending=False).reset_index()
    return sorted_weather_df

def create_season_df(df):
    season_df = df.groupby(by='season').agg({
    'casual': 'sum',
    'countrent': ['mean', 'sum']
})
    season_df.columns = ['casual_rent', 'mean_rent', 'total_rent']
    sorted_season_df = season_df.sort_values(by='casual_rent', ascending=False).reset_index()
    return sorted_season_df

def create_hour_df(df):
    hour_df = df.groupby(by="hourcategory").countrent.sum().sort_values(ascending=False).reset_index()
    return hour_df

def create_rfm_df(df):
    df['datetime'] = pd.to_datetime(df['datetime'])
    rfm_df = df.groupby(by="hour", as_index=False).agg({
        'datetime': 'max',
        'countrent': ['sum', 'count']
    })
    rfm_df.columns = ['hour', 'last_rental', 'monetary', 'frequency']
    latest_timestamp = rfm_df['last_rental'].max()
    rfm_df['recency'] = (latest_timestamp - rfm_df['last_rental']).dt.total_seconds() / 3600
    rfm_df.drop("last_rental", axis=1, inplace=True)

    rfm_df['r_rank'] = rfm_df['recency'].rank(ascending=False)
    rfm_df['f_rank'] = rfm_df['frequency'].rank(ascending=True)
    rfm_df['m_rank'] = rfm_df['monetary'].rank(ascending=True)

    rfm_df['r_rank_norm'] = (rfm_df['r_rank']/rfm_df['r_rank'].max())*100
    rfm_df['f_rank_norm'] = (rfm_df['f_rank']/rfm_df['f_rank'].max())*100
    rfm_df['m_rank_norm'] = (rfm_df['m_rank']/rfm_df['m_rank'].max())*100
    rfm_df.drop(columns=['r_rank', 'f_rank', 'm_rank'], inplace=True)

    rfm_df['RFM_score'] = 0.15*rfm_df['r_rank_norm']+0.28 * rfm_df['f_rank_norm']+0.57*rfm_df['m_rank_norm']
    rfm_df['RFM_score'] *= 0.05
    rfm_df = rfm_df.round(2)

    rfm_df["hoursegment"] = np.where(
        rfm_df['RFM_score'] > 4.5, "Top hours", np.where(
            rfm_df['RFM_score'] > 4, "High value hours", np.where(
                rfm_df['RFM_score'] > 3, "Medium value hours", np.where(
                    rfm_df['RFM_score'] > 1.6, 'Low value hours', 'Lost hours'))))

    hour_segment_df = rfm_df.groupby(by="hoursegment", as_index=False).hour.nunique()
    hour_segment_df.rename(columns={'hour': 'total'}, inplace=True)
    hour_segment_df['hoursegment'] = pd.Categorical(hour_segment_df['hoursegment'], ["Lost hours", "Low value hours", "Medium value hours", "High value hours", "Top hours"])
    return rfm_df, hour_segment_df

#Load cleaned data
all_df = pd.read_csv("all_data.csv")


# Create Streamlit Dashboard
st.title('Bike Sharing Dashboard🚲')

# Sidebar
with st.sidebar:
    st.header('Bike Sharing Company🚲')
    st.image("bike.png")
    filter_option = st.sidebar.selectbox('Pilih Kategori:', ['Weather', 'Season', 'Hour', 'RFM'])

# Display filtered chart
if filter_option == 'Weather':
    st.subheader('Bicycle Users by Weather Condition')
    weather_df = create_weather_df(all_df)
    st.write(weather_df)

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(24, 6))
    colors = ["#335071", "#cedbe9", "#cedbe9", "#cedbe9"]
    bars = sns.barplot(x="weathersit", y="total_rent", data=weather_df.head(), palette=colors, hue="weathersit", ax=ax)
    for bar in bars.patches:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f'{height:.0f}',
            ha='center',
            va='bottom',
            fontsize=12,
            color='black'
        )
    ax.set_ylabel("on Million")
    ax.set_xlabel(None)
    ax.tick_params(axis='y', labelsize=12)
    st.pyplot(fig)
    st.write('Berdasarkan grafik, cuaca "Clear" memiliki jumlah pengguna sepeda lebih banyak dengan total 238,173. Kondisi cuaca "Misty" juga cukup banyak digunakan dengan total 79,952 pengguna, sementara kondisi "Severe Weather" memiliki jumlah pengguna paling sedikit yaitu hanya 223.')

elif filter_option == 'Season':
    st.subheader('Casual Bicycle Users by Season')
    season_df = create_season_df(all_df)
    st.write(season_df)

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(24, 6))
    colors = ["#335071", "#cedbe9", "#cedbe9", "#cedbe9"]
    bars = sns.barplot(x="season", y="casual_rent", data=season_df.head(), palette=colors, hue="season", ax=ax)
    for bar in bars.patches:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f'{height:.0f}',
            ha='center',
            va='bottom',
            fontsize=12,
            color='black'
        )
    ax.set_title("Casual Rent Chart", loc="left", fontsize=18)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='y', labelsize=12)
    st.pyplot(fig)
    st.write('Berdasarkan grafik, musim "Fall" memiliki jumlah pengguna sepeda casual lebih banyak dengan total 226,091. Lalu diikuti musim "Summer" dengan total 203,522 pengguna. Musim "Spring" memiliki jumlah pengguna paling sedikit yaitu 60,622.')

elif filter_option == 'Hour':
    st.subheader('Distribution Of Bicycle Users Between Peak Hours and Off-peak Hours')
    hour_df = create_hour_df(all_df)
    st.write(hour_df)

    def func(pct, allvalues):
        absolute = int(round(pct / 100. * sum(allvalues)))
        return f'{absolute:,} ({pct:.1f}%)'
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        hour_df['countrent'],
        labels=hour_df['hourcategory'],
        autopct=lambda pct: func(pct, hour_df['countrent']),
        startangle=140,
        colors=['#a4bdd5','#7299be'])
    ax.axis('equal')
    st.pyplot(fig)
    st.write('Berdasarkan grafik, waktu "Peak Hour" memiliki jumlah pengguna lebih banyak dengan persentase 50.9% (1,675,779 pengguna) dibandingkan "Off-peak Hour" yang memiliki persentase 49.1% (1,616,900 pengguna).')

elif filter_option == 'RFM':
    rfm_df, hour_segment_df = create_rfm_df(all_df)
    # RFM (1)
    st.subheader('Best Hours Based on RFM Parameters')
    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 6))
    colors = ["#517da6", "#517da6", "#517da6", "#517da6", "#517da6"]

    sns.barplot(y="recency", x="hour", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, hue="hour", legend=False, ax=ax[0])
    ax[0].set_ylabel(None)
    ax[0].set_xlabel(None)
    ax[0].set_title("By Recency (Hour)", loc="center", fontsize=18)
    ax[0].tick_params(axis ='x', labelsize=15)
    for container in ax[0].containers:
        ax[0].bar_label(container, fmt='%.2f', label_type='edge', padding=3)

    sns.barplot(y="frequency", x="hour", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, hue="hour", legend=False, ax=ax[1])
    ax[1].set_ylabel(None)
    ax[1].set_xlabel(None)
    ax[1].set_title("By Frequency (Hour)", loc="center", fontsize=18)
    ax[1].tick_params(axis='x', labelsize=15)
    for container in ax[1].containers:
        ax[1].bar_label(container, fmt='%d', label_type='edge', padding=3)

    sns.barplot(y="monetary", x="hour", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, hue="hour", legend=False, ax=ax[2])
    ax[2].set_ylabel(None)
    ax[2].set_xlabel(None)
    ax[2].set_title("By Monetary (Total Rentals)", loc="center", fontsize=18)
    ax[2].tick_params(axis='x', labelsize=15)
    for container in ax[2].containers:
        ax[2].bar_label(container, fmt='%d', label_type='edge', padding=3)
    st.pyplot(fig)
    st.write("""
    - **Recency:** Berdasarkan grafik, pengguna lebih sering menyewa sepeda pada pukul 19:00, dengan jumlah yang paling sedikit pada pukul 23:00.
    - **Frequency:** Grafik menunjukkan bahwa jam-jam dengan frekuensi penggunaan sepeda tertinggi adalah pukul 13:00, 14:00, 15:00, 16:00, dan 17:00, dengan semua jam tersebut memiliki tingkat frekuensi yang hampir sama.
    - **Monetary:** Berdasarkan grafik, jam dengan total penyewaan tertinggi adalah pukul 17:00 dengan total penyewaan sekitar 305,564, diikuti oleh pukul 18:00 dengan total 273,784.
    """)


    # Additional visualization for RFM
    st.subheader('Hour Segmentation')
    st.table(hour_segment_df)


    # RFM (2)
    st.subheader('Total of Each Segment')
    fig, ax = plt.subplots(figsize=(10, 5))
    colors_ = ["#335071", "#335071", "#335071", "#cedbe9", "#cedbe9"]

    sns.barplot(
        x="total",
        y="hoursegment",
        data=hour_segment_df.sort_values(by="total", ascending=False),
        palette=colors_,
        hue="hoursegment",
        ax=ax
    )

    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='y', labelsize=12)
    for container in ax.containers:
        ax.bar_label(container, fmt='%d', label_type='edge', padding=3)
    st.pyplot(fig)
    st.write('Berdasarkan grafik "Total of Each Segment", terdapat 7 jam yang dikategorikan sebagai "Lost Hours", "Low Value Hours", dan "Medium Value Hours", menunjukkan bahwa sebagian besar jam memiliki nilai kontribusi rendah hingga sedang. Hanya ada 2 jam yang termasuk "High Value Hours" dan 1 jam yang masuk kategori "Top Hours", yang menunjukkan nilai kontribusi tertinggi. Hal ini berarti terdapat banyak jam yang kurang peminat dalam menggunakan sepeda sharing, sementara hanya sedikit jam yang sangat produktif.')


st.caption('Copyright © Shintyadhita 2024')
