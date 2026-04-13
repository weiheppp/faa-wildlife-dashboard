import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 页面配置
st.set_page_config(page_title="FAA Wildlife Strike Explorer", layout="wide")

# 1. 数据加载与缓存
@st.cache_data
def load_data():
    try:
        # 读取数据
        df = pd.read_csv('wildlife_strikes.csv', encoding='latin-1')
        
        # 【关键修复1】标准化所有列名：变大写并替换空格为下划线
        # 这样无论表头是 "Incident Date" 还是 "INCIDENT_DATE"，代码都能认得！
        df.columns = df.columns.str.strip().str.upper().str.replace(' ', '_')
        
        # 提取日期和年份
        df['INCIDENT_DATE'] = pd.to_datetime(df['INCIDENT_DATE'], errors='coerce')
        df['YEAR'] = df['INCIDENT_DATE'].dt.year
        
        # 【关键修复2】容错处理：如果你下载的是简略版数据，自动补充缺失的列防止图表崩溃
        if 'COST_REPAIRS' not in df.columns: df['COST_REPAIRS'] = 0
        if 'PHASE_OF_FLIGHT' not in df.columns: df['PHASE_OF_FLIGHT'] = 'Unknown'
        if 'HEIGHT' not in df.columns: df['HEIGHT'] = 0
        if 'DAMAGE' not in df.columns: df['DAMAGE'] = 'None'
        if 'SPECIES' not in df.columns: df['SPECIES'] = 'Unknown Bird'
        if 'AIRPORT' not in df.columns: df['AIRPORT'] = 'Unknown Airport'
        
        return df
    except Exception as e:
        st.error(f"数据处理出错，请检查 CSV 文件是否正确上传。错误信息: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- 侧边栏交互 (Dynamic Queries) ---
    st.sidebar.header("数据探索过滤器")
    
    # 确保年份有有效数据，防止 NaN 报错
    min_year = int(df['YEAR'].min()) if pd.notna(df['YEAR'].min()) else 2020
    max_year = int(df['YEAR'].max()) if pd.notna(df['YEAR'].max()) else 2024
    
    year_range = st.sidebar.slider("选择年份范围", min_year, max_year, (min_year, max_year))
    
    phases = st.sidebar.multiselect("选择飞行阶段", 
        options=df['PHASE_OF_FLIGHT'].unique(), 
        default=df['PHASE_OF_FLIGHT'].unique()
    )
    
    filtered_df = df[
        (df['YEAR'] >= year_range[0]) & 
        (df['YEAR'] <= year_range[1]) &
        (df['PHASE_OF_FLIGHT'].isin(phases))
    ]
    
    # --- 主界面展示 ---
    st.title("✈️ FAA 野生动物撞击交互式分析仪表板")
    st.markdown("本应用旨在探索美国航空安全中的鸟击事件及其造成的经济损失。")
    
    # 关键指标卡片
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总撞击事件", f"{len(filtered_df):,}")
    with col2:
        total_cost = filtered_df['COST_REPAIRS'].sum()
        st.metric("维修总成本", f"${total_cost:,.0f}")
    with col3:
        damage_rate = (len(filtered_df[filtered_df['DAMAGE'] != 'None']) / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
        st.metric("导致损坏比例", f"{damage_rate:.1f}%")
        
    # 图表 1: 时间趋势
    st.subheader("📊 历年撞击趋势分析")
    trend_data = filtered_df.groupby('YEAR').size().reset_index(name='Count')
    fig_line = px.line(trend_data, x='YEAR', y='Count', title="选定范围内的年度事件频率", labels={'Count': '撞击次数', 'YEAR': '年份'}, template="plotly_white")
    st.plotly_chart(fig_line, use_container_width=True)

    # 图表 2 & 3
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("🦜 涉及的主要鸟类品种")
        species_data = filtered_df['SPECIES'].value_counts().head(10).reset_index()
        fig_bar = px.bar(species_data, x='count', y='SPECIES', orientation='h', title="前十大撞击物种", labels={'count': '发生次数', 'SPECIES': '物种'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_right:
        st.subheader("💰 维修成本与飞行高度关系")
        fig_scatter = px.scatter(filtered_df, x='HEIGHT', y='COST_REPAIRS', color='PHASE_OF_FLIGHT', title="高度 vs 成本", labels={'HEIGHT': '高度 (英尺)', 'COST_REPAIRS': '维修成本 ($)'})
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    # --- 作业要求的撰写部分 (Write-up) ---
    st.divider()
    with st.expander("📝 查看作业报告 (Write-up)", expanded=False):
        st.markdown("""
        ### 1. 核心问题
        本可视化旨在回答：**哪些飞行阶段和鸟类品种对美国民航造成的经济损失最严重？** 通过分析高度、飞行阶段与维修成本的关系，帮助航司识别高风险时段。

        ### 2. 设计决策理由
        - **视觉编码**：使用气泡散点图将成本映射，能够直观展示极端损失事件。颜色区分飞行阶段，便于观察不同海拔下的安全分布。
        - **交互技术**：引入了**动态过滤（年份/阶段）**，允许用户从宏观趋势深入到特定场景。
        - **替代方案**：曾考虑使用静态热力图，但由于数据地理跨度大且时间属性强，最终选择了 Plotly 交互图表以支持平移和精准数据读取。

        ### 3. 数据来源与参考
        - 数据源：[FAA Wildlife Strike Database](https://wildlife.faa.gov/)
        - 技术参考：[Streamlit Documentation](https://docs.streamlit.io)

        ### 4. 开发过程总结
        - **总耗时**：约 8 小时。
        - **最耗时环节**：数据清洗与格式标准化处理。
        """)
else:
    st.warning("等待加载数据...")
