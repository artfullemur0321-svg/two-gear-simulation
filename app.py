# MAE 101 - Streamlit gear-driven winch simulator
import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Two-Gear Lifting Simulator", layout="wide")
G = 9.81

def cylinder(radius, x0, x1, cy=0, cz=0, color='#8796a5', name='shaft'):
    a = np.linspace(0, 2*np.pi, 40)
    x = np.array([x0, x1])[:,None] * np.ones((1,len(a)))
    y = cy + radius*np.cos(a)[None,:] * np.ones((2,1))
    z = cz + radius*np.sin(a)[None,:] * np.ones((2,1))
    return go.Surface(x=x,y=y,z=z,colorscale=[[0,color],[1,color]],showscale=False,name=name,hoverinfo='skip')

def gear_mesh(teeth, pitch_radius, cx, cz, phase, color, name):
    # Stylized gear teeth, not an involute tooth-contact model.
    n = teeth * 8
    a = np.linspace(0,2*np.pi,n+1)
    tooth = np.cos(teeth*(a-phase))
    rr = pitch_radius*(0.94 + 0.10*(tooth > 0.15))
    yy = cx + rr*np.cos(a)
    zz = cz + rr*np.sin(a)
    return go.Scatter3d(x=np.zeros_like(a),y=yy,z=zz,mode='lines',
        line=dict(color=color,width=9),name=name,hoverinfo='skip')

def make_scene(n1,n2,t1,rpm,eff,drum_r,mass,time_s):
    ratio = n2/n1
    t2 = t1*ratio*eff/100
    rpm2 = rpm/ratio
    omega2 = rpm2*2*np.pi/60
    power = t2*omega2
    max_mass = t2/(G*drum_r)
    lifting = mass < max_mass - 1e-9
    # Visualization is schematic: geometric gear size is scaled for readability.
    r1 = 0.18
    r2 = r1*ratio
    center2 = r1+r2
    angle1 = rpm*2*np.pi*time_s/60
    angle2 = -angle1/ratio + np.pi/n2
    traces = [
        gear_mesh(n1,r1,0,0,angle1,'#2584bb','Input gear'),
        gear_mesh(n2,r2,center2,0,angle2,'#e0a03b','Output gear'),
        cylinder(0.035,-0.18,0.18,0,0,'#8995a4','Input shaft'),
        cylinder(0.035,-0.18,0.60,center2,0,'#8995a4','Output shaft'),
        cylinder(0.095,0.35,0.52,center2,0,'#aab3bd','Winding drum'),
    ]
    # Drum is along the shaft axis (X). The cable exits below the drum.
    # Lift position is capped to keep the illustrative animation visible.
    rise = min(0.38, max(0,time_s*drum_r*omega2)) if lifting else 0
    top = -0.095
    bottom = -0.85 + rise
    traces.append(go.Scatter3d(x=[0.45,0.45],y=[center2+0.095,center2+0.095],z=[top,bottom],
        mode='lines',line=dict(color='#626e7b',width=5),name='Cable'))
    traces.append(go.Scatter3d(x=[0.45],y=[center2+0.095],z=[bottom-0.06],mode='markers+text',
        marker=dict(size=14,color='#bd6548',symbol='square'),text=[f'{mass:.2f} kg'],
        textposition='bottom center',name='Load'))
    fig=go.Figure(data=traces)
    fig.update_layout(height=530,margin=dict(l=0,r=0,t=35,b=0),
        title='Schematic 3D gear-driven winch',
        scene=dict(xaxis=dict(title='Shaft axis'),yaxis=dict(title='Gear positions'),
                   zaxis=dict(title='Height'),aspectmode='data'),
        legend=dict(orientation='h',y=-0.08))
    return fig,ratio,t2,rpm2,power,max_mass,lifting


st.title("Two-Gear Mechanical Lifting Simulator")
st.caption("MAE 101 | Theoretical gear-reduction and lifting model")
with st.sidebar:
    st.header("Known parameters")
    n1 = st.slider("Input gear teeth", 8, 48, 12)
    n2 = st.slider("Output gear teeth", 8, 72, 36)
    t1 = st.slider("Input torque (N·m)", 0.05, 1.0, 0.20, 0.05)
    rpm = st.slider("Input speed (RPM)", 5, 180, 60, 5)
    eff = st.slider("Assumed efficiency (%)", 50, 100, 80, 5)
    drum = st.slider("Drum radius (m)", 0.01, 0.10, 0.02, 0.005, format="%.3f")
    mass = st.slider("Hanging load (kg)", 0.1, 6.0, 2.0, 0.1)
    time = st.slider("Animation time (s)", 0.0, 8.0, 0.0, 0.25)

fig, gr, tout, rout, pout, mmax, can_lift = make_scene(n1,n2,t1,rpm,eff,drum,mass,time)
st.plotly_chart(fig, use_container_width=True)
a,b,c=st.columns(3)
a.metric("Gear ratio", f"{gr:.2f}:1")
b.metric("Output torque", f"{tout:.3f} N·m")
c.metric("Output speed", f"{rout:.2f} RPM")
d,e,f=st.columns(3)
d.metric("Output power", f"{pout:.3f} W")
e.metric("Max steady-load mass", f"{mmax:.2f} kg")
f.metric("Lifting speed", f"{drum*rout*2*np.pi/60:.4f} m/s")
if can_lift:
    st.success("Predicted torque is sufficient to lift the selected load under the model assumptions.")
else:
    st.warning("Predicted torque is insufficient to lift the selected load under the model assumptions.")
