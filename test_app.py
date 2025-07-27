import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title='eFootball Player Model Visualizer', layout='wide')

st.title('eFootball Player Model Visualizer')

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("player_models.csv")

df = load_data()

player_names = df["Name"].tolist()

# Player selection
col1, col2 = st.columns(2)
with col1:
    player1 = st.selectbox("Choose player 1", player_names, index=0)
with col2:
    player2 = st.selectbox("Choose player 2", player_names, index=1)

def get_player_data(name):
    d = df[df['Name'] == name].iloc[0]
    return {
        "name": d["Name"],
        "leg": d["Leg_Length"],
        "arm": d["Arm_Length"],
        "neck": d["Neck_Length"],
        "shoulder": d["Shoulder_Width"],
        "height": d["Height_cm"],
        "position": d["Position"],
        "club": d["Club"]
    }

def create_skeleton(player, xshift=0):
    # Scale factors
    height = player["height"]
    scale = height / 180

    base_leg = 50  # pixels
    base_arm = 35
    base_neck = 12
    base_shoulder = 25

    # Calculate points (all coordinates are 2D; y up, x right)
    # xshift centers separate skeletons
    hip_x, hip_y = xshift, 0

    knee_y = hip_y + base_leg * 0.5 * scale * (player["leg"] / 10)
    foot_y = knee_y + base_leg * 0.5 * scale * (player["leg"] / 10)
    shoulder_y = foot_y + base_leg * scale * 0.1

    left_shoulder = hip_x - base_shoulder * scale * (player["shoulder"] / 10)
    right_shoulder = hip_x + base_shoulder * scale * (player["shoulder"] / 10)
    left_hand = left_shoulder - base_arm * scale * (player["arm"] / 10)
    right_hand = right_shoulder + base_arm * scale * (player["arm"] / 10)
    head_y = shoulder_y + base_neck * scale * (player["neck"] / 10)

    # Collect lines for skeleton
    lines = [
        # Legs: hip to knee to foot
        ((hip_x, hip_y), (hip_x, knee_y), 'Leg', f"Leg Length: {player['leg']}"),
        ((hip_x, knee_y), (hip_x, foot_y), 'Leg', f"Leg Length: {player['leg']}"),
        # Torso: hip to shoulder
        ((hip_x, hip_y), (hip_x, shoulder_y), 'Torso', f"Shoulder Width: {player['shoulder']}"),
        # Shoulders
        ((left_shoulder, shoulder_y), (right_shoulder, shoulder_y), 'Shoulders', f"Shoulder Width: {player['shoulder']}"),
        # Arms
        ((left_shoulder, shoulder_y), (left_hand, shoulder_y), 'Arm', f"Arm Length: {player['arm']}"),
        ((right_shoulder, shoulder_y), (right_hand, shoulder_y), 'Arm', f"Arm Length: {player['arm']}"),
        # Neck
        ((hip_x, shoulder_y), (hip_x, head_y), 'Neck', f"Neck Length: {player['neck']}"),
    ]

    # Points of interest for hover: (x, y, label, value)
    points = [
        (left_hand, shoulder_y, "Arm Length", player['arm']),
        (right_hand, shoulder_y, "Arm Length", player['arm']),
        (hip_x, foot_y, "Leg Length", player['leg']),
        (hip_x, (shoulder_y + head_y) / 2, "Neck Length", player['neck']),
        (hip_x, shoulder_y, "Shoulder Width", player['shoulder']),
        (hip_x, head_y + 10, "Height", player['height']),
    ]

    # Store all coordinates for plotting
    return lines, points, hip_x, head_y, foot_y

# Plotly fig
def plot_skeleton(player, xshift, color, side="left"):
    lines, points, hip_x, head_y, foot_y = create_skeleton(player, xshift=xshift)
    data = []
    # Skeleton lines
    bone_colors = {
        'Leg': color,
        'Arm': "blue",
        'Neck': "green",
        'Shoulders': "purple",
        'Torso': "orange"
    }
    for (start, end, part, label) in lines:
        data.append(
            go.Scatter(
                x=[start[0], end[0]],
                y=[start[1], end[1]],
                mode='lines',
                line=dict(width=7 if part == 'Leg' else 5, color=bone_colors.get(part, "black")),
                name=f"{part}",
                hoverinfo='text',
                showlegend=False,
                hovertext=label
            )
        )
    # Skeleton head (as a circle)
    data.append(
        go.Scatter(
            x=[hip_x],
            y=[head_y + 10],
            mode='markers',
            marker=dict(color='red', size=22, line=dict(width=2, color="black")),
            hoverinfo='text', hovertext=f"Height: {player['height']}",
            showlegend=False
        )
    )
    # Hover-able points for body parts
    for (x, y, label, val) in points:
        data.append(
            go.Scatter(
                x=[x], y=[y],
                mode='markers+text',
                marker=dict(color='rgba(0,0,255,0.15)', size=28),
                hoverinfo='text',
                hovertext=f"{label}: {val}",
                text=None,
                showlegend=False
            )
        )
    # Player name
    data.append(
        go.Scatter(
            x=[hip_x],
            y=[foot_y - 25],
            mode='text',
            text=[player['name']],
            textposition="bottom center",
            textfont=dict(size=17, color=color, family="Arial Black"),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    # Height side-bar
    for dx in [-45, 45]:
        data.append(
            go.Scatter(
                x=[hip_x + dx, hip_x + dx],
                y=[foot_y, head_y + 10],
                mode='lines',
                line=dict(color='gray', width=2, dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            )
        )
        # Label
        data.append(
            go.Scatter(
                x=[hip_x + dx],
                y=[(foot_y + head_y + 10)/2],
                mode='text',
                text=[f"{player['height']} cm"],
                textfont=dict(size=13, color="gray"),
                showlegend=False,
                hoverinfo='skip',
                textposition="middle right" if dx>0 else "middle left"
            )
        )
    return data

data1 = get_player_data(player1)
data2 = get_player_data(player2)

# Visual separation between left/right
sep = 120

skeleton1 = plot_skeleton(data1, -sep, "crimson", side="left")
skeleton2 = plot_skeleton(data2, sep, "darkblue", side="right")

fig = go.Figure(data=skeleton1 + skeleton2)

fig.update_layout(
    width=900, height=600,
    margin=dict(l=0, r=0, t=40, b=0),
    xaxis=dict(showgrid=False, zeroline=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, visible=False),
    plot_bgcolor="white",
)

st.plotly_chart(fig, use_container_width=True)

# Display player data tables
left, right = st.columns(2)
with left:
    st.subheader(f"{player1} ({data1['position']}, {data1['club']})")
    st.markdown(
        f"""- **Leg Length:** {data1['leg']}
- **Arm Length:** {data1['arm']}
- **Neck Length:** {data1['neck']}
- **Shoulder Width:** {data1['shoulder']}
- **Height:** {data1['height']} cm""")
with right:
    st.subheader(f"{player2} ({data2['position']}, {data2['club']})")
    st.markdown(
        f"""- **Leg Length:** {data2['leg']}
- **Arm Length:** {data2['arm']}
- **Neck Length:** {data2['neck']}
- **Shoulder Width:** {data2['shoulder']}
- **Height:** {data2['height']} cm""")

st.info("""
**Instructions:**  
- Choose any two players.  
- Hover over arms, legs, neck, or height bar to see the exact attribute values as tooltips.  
- Player names shown below figures.  
- Height scale shown on sides for context.
""")
