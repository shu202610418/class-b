# ===== 1. 라이브러리 불러오기 =====
import streamlit as st
import pandas as pd
import plotly.express as px

# 가장 먼저 실행되는 Streamlit 페이지 설정 (와이드 레이아웃)
st.set_page_config(page_title="Titanic 대시보드", layout="wide")


# ===== 2. 데이터 로드 함수 =====
# @st.cache_data를 사용하여 titanic.csv 파일을 한 번만 읽고 캐싱
@st.cache_data
def load_data():
    return pd.read_csv("titanic.csv")


# ===== 3. 데이터 필터링 및 분석·시각화 함수 =====
# 성별, 객실 등급, 나이 범위를 조건으로 데이터를 필터링하는 함수
def filter_data(df, sexes, classes, age_range):
    # age_range 튜플에서 최소 나이와 최대 나이 분리하기
    min_age, max_age = age_range

    # 성별 조건: 'sex' 열의 값이 sexes 목록에 포함되는지 확인
    cond_sex = df["sex"].isin(sexes)

    # 객실 등급 조건: 'pclass' 열의 값이 classes 목록에 포함되는지 확인
    cond_class = df["pclass"].isin(classes)

    # 나이 슬라이더가 전체 범위(0~80)이면 나이 결측치(NaN)도 포함하고, 아니면 범위 내 값만 선택 # [수정]
    if min_age == 0 and max_age == 80: # [수정]
        cond_age = (df["age"].between(min_age, max_age, inclusive="both")) | (df["age"].isna()) # [수정]
    else: # [수정]
        cond_age = df["age"].between(min_age, max_age, inclusive="both") # [수정]

    # 세 가지 조건(& 연산자 사용)을 모두 만족하는 행만 추출하여 반환
    filtered_df = df[cond_sex & cond_class & cond_age]
    return filtered_df


# 대시보드 상단 숫자 카드용 KPI 지표(승객 수, 생존율, 평균 나이)를 계산하는 함수
def kpi(df):
    # 전달받은 데이터프레임이 비어 있으면 (0, 0, 0) 반환
    if df.empty:
        return (0, 0, 0)

    # 승객 수 계산
    passenger_count = len(df)

    # 생존율(%) 계산: 'survived' 열의 평균에 100을 곱한 뒤 소수 첫째 자리로 반올림
    survival_rate = round(df["survived"].mean() * 100, 1)

    # 평균 나이 계산: 'age' 열의 평균을 구한 뒤 소수 첫째 자리로 반올림
    avg_age = round(df["age"].mean(), 1)

    # 승객 수, 생존율(%), 평균 나이 순서로 3개 값 반환
    return (passenger_count, survival_rate, avg_age)


# 객실 등급(pclass)별 생존율(%) 막대그래프를 생성하고 fig를 반환하는 함수
def class_rate_bar(df):
    # 객실 등급별 생존 비율(0~1)을 구한 뒤 백분율(%)과 소수 첫째 자리로 변환
    rate_df = (
        df.groupby("pclass", as_index=False)["survived"]
        .mean()
        .assign(survival_rate=lambda x: (x["survived"] * 100).round(1))
    )

    # 객실 등급별 생존율(%) 막대그래프 생성 및 막대 위에 값(text) 표시
    fig = px.bar(
        rate_df,
        x="pclass",
        y="survival_rate",
        text="survival_rate",
        title="객실 등급별 생존율(%)",
        labels={"pclass": "객실 등급", "survival_rate": "생존율 (%)"},
    )

    # 막대 상단 바깥쪽에 값이 깔끔하게 보이도록 텍스트 위치 지정
    fig.update_traces(textposition="outside")
    return fig


# 나이(age) 히스토그램을 생성하고 fig를 반환하는 함수
def age_hist(df):
    # 생존 여부(survived)를 색상(color)으로 구분하고 투명도(opacity=0.6)를 적용한 히스토그램 생성
    fig = px.histogram(
        df,
        x="age",
        color="survived",
        opacity=0.6,
        title="생존 여부별 승객 나이 분포",
        labels={"age": "나이", "survived": "생존 여부 (0=사망, 1=생존)"},
    )

    # 히스토그램 막대를 겹쳐서 표시하도록 barmode를 "overlay"로 설정
    fig.update_layout(barmode="overlay")
    return fig


# ===== 4. 데이터 불러오기 및 페이지 제목 설정 =====
df = load_data()

# 대시보드 상단 제목 표시
st.title("타이타닉, 누가살아남았나?")


# ===== 5. 사이드바 필터 구성 =====
st.sidebar.header("검색 조건 필터")

# 성별 선택 (기본값: 전체 선택)
sex_options = df["sex"].dropna().unique().tolist()
selected_sexes = st.sidebar.multiselect(
    "성별 선택",
    options=sex_options,
    default=sex_options,
)

# 객실 등급 선택 (기본값: 1, 2, 3 모두 선택)
class_options = sorted(df["pclass"].dropna().unique().tolist())
selected_classes = st.sidebar.multiselect(
    "객실 등급 선택",
    options=class_options,
    default=class_options,
)

# 나이 범위 슬라이더 (0~80세, 기본값: 전체 범위)
selected_age_range = st.sidebar.slider(
    "나이 범위 선택",
    min_value=0,
    max_value=80,
    value=(0, 80),
)


# ===== 6. 데이터 필터링 및 본문 출력 =====
# 성별이나 객실 등급을 하나도 선택하지 않으면 경고 안내 후 실행 중단 # [수정]
if not selected_sexes or not selected_classes: # [수정]
    st.warning("성별과 객실 등급을 각각 1개 이상 선택해 주세요.") # [수정]
    st.stop() # [수정]

# 사이드바에서 선택한 조건으로 데이터 필터링 실행
filtered_df = filter_data(df, selected_sexes, selected_classes, selected_age_range)

# 필터링 결과가 0명이면 안내 메시지 출력 후 실행 중단 # [수정]
if len(filtered_df) == 0: # [수정]
    st.info("조건에 맞는승객이없습니다") # [수정]
    st.stop() # [수정]

# 필터링된 데이터로 승객 수, 생존율(%), 평균 나이 계산
passenger_count, survival_rate, avg_age = kpi(filtered_df)

# KPI 카드 3개를 가로로 배치할 3열 생성
col1, col2, col3 = st.columns(3)

# 첫 번째 열에 승객 수(명) 카드 표시
col1.metric("승객수(명)", f"{passenger_count}명")

# 두 번째 열에 생존율(%) 카드 표시
col2.metric("생존율(%)", f"{survival_rate}%")

# 세 번째 열에 평균 나이(세) 카드 표시
col3.metric("평균나이(세)", f"{avg_age}세")

# 차트 2개를 좌우로 배치할 2열 생성
chart_col1, chart_col2 = st.columns(2)

# 왼쪽 열에 객실 등급별 생존율 막대그래프 표시
chart_col1.plotly_chart(class_rate_bar(filtered_df), use_container_width=True)

# 오른쪽 열에 생존 여부별 나이 히스토그램 표시
chart_col2.plotly_chart(age_hist(filtered_df), use_container_width=True)

# 맨 아래 접이식 영역("데이터보기") 안에 필터링된 데이터프레임 표시
with st.expander("데이터보기"):
    st.dataframe(filtered_df)
