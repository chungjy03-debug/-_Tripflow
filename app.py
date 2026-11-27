# TripFlow Streamlit 앱의 시작 화면으로, 제목만 보여주고 메뉴는 pages/의 기본 내비게이션을 쓴다.
import streamlit as st

st.set_page_config(page_title="TripFlow", layout="wide")
st.title("TripFlow")
st.write("왼쪽 메뉴에서 페이지를 선택하세요.")
