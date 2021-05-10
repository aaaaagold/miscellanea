"use strict";

class minesweeper{
//private:
	_none(){}
	_xy2idx(x,y){
		return this._w*y+x;
	}
	_isValidXY(x,y){
		return x>=0&&x<this._w&&y>=0&&y<this._h;
	}
	_nearBomb(x,y){
		let rtv=0;
		for(let j=-1;j!==2;++j){ for(let i=-1;i!==2;++i){
			if(!this._isValidXY(x+i,y+j)) continue;
			rtv+=this._bombMap[this._xy2idx(x+i,y+j)]|0;
		} }
		return rtv;
	}
	_initQ(){
		//this._q.length=0;
		this._qf=0;
		this._qr=0;
	}
	_capQ(){ return (this._w*this._h)<<4; }
	_pushQ(obj){
		this._q[this._qr++]=obj;
		if(this._qr>=this._capQ()) this._qr=0;
	}
	_popQ(){
		const rtv=this._q[this._qf++];
		if(this._qf>=this._capQ()) this._qf=0;
		return rtv;
	}
	_lenQ(){
		return (this._qr<this._qf?this._capQ():0)+this._qr-this._qf;
	}
//public:
	constructor(w,h,cnt,kargs){
		this._w=w||1;
		this._h=h||1;
		this._c=cnt||0;
		{ const sz=this._w*this._h;
		if(!(this._c<=sz)) this._c=sz; }
		this._q=[];
		this._qf=0;
		this._qr=0;
		this._bombMap=[];
		this._revealMap=[]; // 0-like: init ; 1: revealed ; 2: flagged
		kargs=kargs||{};
		['onboom','ondone','onflag','onreveal','onunflag'].forEach(x=>{
			this["_"+x]=(x in kargs)?kargs[x]:0;
		});
		this.initGame();
	}
	initGame(){
		this._revealMap.length=this._bombMap.length=0;
		this._cnt=(this._revealMap.length=this._bombMap.length=this._w*this._h)-this._c;
		const candi=[],max=this._xy2idx(this._w-1,this._h-1)+1;
		for(let x=0;x!==max;++x) candi.push(x);
		for(let r=this._c;r--;){
			const idx1=~~(Math.random()*candi.length);
			const idx2=candi.length-1;
			{ const tmp=candi[idx1]; candi[idx1]=candi[idx2]; candi[idx2]=tmp; }
			this._bombMap[candi.pop()]=true;
		}
		return this;
	}
	canReveal(x,y){ return this._revealMap[this._xy2idx(x,y)]!==1; }
	reveal(x,y){
		if(!this._cnt||this.isFlagged(x,y)||!this._isValidXY(x,y)||!this.canReveal(x,y)) return;
		const idx=this._xy2idx(x,y);
		if(this._revealMap[idx]) return;
		if(this._bombMap[idx]){
			this._revealMap[idx]=true;
			return this.onBoom(x,y);
		}
		
		this._initQ();
		this._pushQ(idx);
		while(this._lenQ()){
			const curr=this._popQ();
			if(this._revealMap[curr]) continue;
			this._revealMap[curr]=1;
			--this._cnt;
			const x=curr%this._w;
			const y=~~(curr/this._w);
			const cnt=this._nearBomb(x,y);
			this.onReveal(x,y,cnt);
			if(cnt) continue;
			for(let j=-1;j!==2;++j){ for(let i=-1;i!==2;++i){
				if(!this._isValidXY(x+i,y+j)) continue;
				this._pushQ(this._xy2idx(x+i,y+j));
			} }
		}
		if(!this._cnt) this.onDone(x,y);
	}
	isFlagged(x,y){ return this._revealMap[this._xy2idx(x,y)]===2; }
	flagIt(x,y){
		if(!this.canReveal(x,y)) return;
		const b=this.isFlagged(x,y);
		this._revealMap[this._xy2idx(x,y)]=b?0:2;
		b?this.onUnflag(x,y):this.onFlag(x,y);
	}
};
Object.defineProperties(minesweeper.prototype,{
onBoom:{
	get:function(){ return this._onboom&&this._onboom.constructor===Function?this._onboom:this._none; },
	set:function(rhs){ return this._onboom=rhs; },
},
onDone:{
	get:function(){ return this._ondone&&this._ondone.constructor===Function?this._ondone:this._none; },
	set:function(rhs){ return this._ondone=rhs; },
},
onFlag:{
	get:function(){ return this._onflag&&this._onflag.constructor===Function?this._onflag:this._none; },
	set:function(rhs){ return this._onflag=rhs; },
},
onReveal:{
	get:function(){ return this._onreveal&&this._onreveal.constructor===Function?this._onreveal:this._none; },
	set:function(rhs){ return this._onreveal=rhs; },
},
onUnflag:{
	get:function(){ return this._onunflag&&this._onunflag.constructor===Function?this._onunflag:this._none; },
	set:function(rhs){ return this._onunflag=rhs; },
},
});
