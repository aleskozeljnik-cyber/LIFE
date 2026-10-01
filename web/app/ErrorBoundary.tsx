"use client";

import { Component, ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <main style={{minHeight:"100vh",display:"grid",placeItems:"center",padding:40,fontFamily:"system-ui",background:"#eef1ed",color:"#17211d"}}>
          <div style={{maxWidth:720,padding:32,border:"1px solid #d9ded8",borderRadius:24,background:"#fff"}}>
            <div style={{fontSize:12,letterSpacing:".14em",textTransform:"uppercase",color:"#8a918c"}}>LIFE · RUNTIME ERROR</div>
            <h1 style={{fontSize:32,margin:"12px 0"}}>LIFE se ni mogel zagnati.</h1>
            <p style={{color:"#69716c"}}>Production frontend se je naložil, vendar je pri izvajanju prišlo do napake.</p>
            <pre style={{whiteSpace:"pre-wrap",fontSize:13,background:"#f3f5f2",padding:16,borderRadius:12,overflow:"auto"}}>{this.state.error?.stack || this.state.error?.message}</pre>
            <button onClick={()=>window.location.reload()} style={{marginTop:16,padding:"10px 16px",borderRadius:10,border:"1px solid #cfd6cf",background:"#173b2d",color:"#fff"}}>Osveži LIFE</button>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}
