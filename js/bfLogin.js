// current version not completed
// still need to install web plugin; .exe plugin is not needed

// beanfun login
// need to paste on console or,
// you may add the following to bookmarks to trigger
// javascript:document.head.appendChild((function(){ let t=document.createElement("script"); t.setAttribute("type","text/javascript"); t.setAttribute("src","https://aaaaagold.github.io/miscellanea/js/bfLogin.js"); return t; })());


(function(){


let d=document,q={};
let jurl=function jurl(url,method,data,callback){
	// callback(xml.responseText);
	let ajaxdom;
	let xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4) {
			let s=this.status.toString();
			if(s.length==3 && s.slice(0,1)=='2'){
				//console.log(ajaxdom=new DOMParser().parseFromString(this.responseText,"text/html"));
				if(typeof(callback)=="function"){
					callback(this.responseText);
				}
			}
		}
	};
	xhttp.open(method,url,true);
	xhttp.send(method==="GET"?undefined:data);
},hostAt="https://tw.beanfun.com/";
let rt,otp,svc,game,acc; // DOM
let accQSerial=0,infoQSerial=0; // prevent conflict
let genBlock=function genBlock(){
	
	rt=q.ce("div").sa("id","root").sa("class","maxToParent");
	rt.ac( otp=q.ce("div").sa("id","otp1").sa("class","otp").ac(q.ce("div").at("otp:")) );
	svc=q.ce("div").sa("class","svc");
	d.body.ac(rt.ac(svc));
	svc.ac(q.ce("div").ac( game=q.ce("div").sa("id","games1").ac(q.ce("div").at("games:")) ));
	svc.ac(q.ce("div").ac( acc=q.ce("div").sa("id","accs1").ac(q.ce("div").at("accounts:")) ));
};
let clearCurrent=function clearCurrent(){
	d.write('.');
	d.head.innerHTML="";
	if(q.ge("bfMinLoginCss")==null){
		let css=q.ce("style").sa("id","bfMinLoginCss");
		css.at(".maxToParent{width:100%;height:100%;padding:0px;margin:0px;border:0px solid rgba(0,0,0,0);}");
		css.at(".__>div{display:inline-block;}");
		css.at(".sel{background-color:rgba(255,255,0,0.5);}");
		css.at("body{position:absolute;background-color:#000000;color:#FFFFFF;}");
		css.at("#root{position:relative;}");
		// OTP
		css.at(".otp{position:relative;height:11%;}");
		css.at(".otp>div{margin:11px 0px 0px 11px;display:inline-block;}");
		// services
		css.at(".svc{position:relative;width:100%;height:89%;}");
		// cut w:50.50
		css.at(".svc>div{position:absolute;top:0%;bottom:0%;width:50%;margin:0px;border:0px solid rgba(0,0,0,0);padding:0px;display:inline-block;}");
		css.at(".svc>div:nth-child(1){left:0%;}"); // games
		css.at(".svc>div:nth-child(2){right:0%;}"); // accs
		//css.at(".svc>.games{left:0%;}.svc>.accs{right:0%;}");
		// scroll-y
		css.at(".svc>div>div{position:relative;width:100%;height:100%;overflow-y:scroll;margin:0px;border:0px solid rgba(0,0,0,0);padding:0px;}");
		// contents
		css.at(".svc>div>div>div{margin:11px;border-left:11px solid rgba(255,255,255,0.5);padding:0px 0px 0px 11px;}");
		css.at(".svc>div>div>div:hover{background-color:rgba(255,255,255,0.5);}");
		d.head.ac(css);
		console.log("css added");
	}
	d.body.innerHTML="";
	d.body.removeAttribute("style");
	d.body.sa("class","maxToParent");
};
let desDecrypt=function(s){
	
	let map_ip=[
58,50,42,34,26,18,10,2,
60,52,44,36,28,20,12,4,
62,54,46,38,30,22,14,6,
64,56,48,40,32,24,16,8,
57,49,41,33,25,17,9,1,
59,51,43,35,27,19,11,3,
61,53,45,37,29,21,13,5,
63,55,47,39,31,23,15,7];

	let map_pc1=[
57,49,41,33,25,17,9,
1,58,50,42,34,26,18,
10,2,59,51,43,35,27,
19,11,3,60,52,44,36,
63,55,47,39,31,23,15,
7,62,54,46,38,30,22,
14,6,61,53,45,37,29,
21,13,5,28,20,12,4];

	let map_pc2=[
14,17,11,24,1,5,
3,28,15,6,21,10,
23,19,12,4,26,8,
16,7,27,20,13,2,
41,52,31,37,47,55,
30,40,51,45,33,48,
44,49,39,56,34,53,
46,42,50,36,29,32];

	let map_e=[
32,1,2,3,4,5,
4,5,6,7,8,9,
8,9,10,11,12,13,
12,13,14,15,16,17,
16,17,18,19,20,21,
20,21,22,23,24,25,
24,25,26,27,28,29,
28,29,30,31,32,1];

	let map_p=[
16,7,20,21,29,12,28,17,
1,15,23,26,5,18,31,10,
2,8,24,14,32,27,3,9,
19,13,30,6,22,11,4,25];

	let map_fp=[
40,8,48,16,56,24,64,32,
39,7,47,15,55,23,63,31,
38,6,46,14,54,22,62,30,
37,5,45,13,53,21,61,29,
36,4,44,12,52,20,60,28,
35,3,43,11,51,19,59,27,
34,2,42,10,50,18,58,26,
33,1,41,9,49,17,57,25];

	let map_shift=[
1,1,2,2,
2,2,2,2,
1,2,2,2,
2,2,2,1];

	let s1=[
14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7,
0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8,
4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0,
15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13
	];
	let s2=[
15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10,
3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5,
0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15,
13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9
	];
	let s3=[
10,0,9,14,6,3,15,5,1,13,12,7,11,4,2,8,
13,7,0,9,3,4,6,10,2,8,5,14,12,11,15,1,
13,6,4,9,8,15,3,0,11,1,2,12,5,10,14,7,
1,10,13,0,6,9,8,7,4,15,14,3,11,5,2,12
	];
	let s4=[
7,13,14,3,0,6,9,10,1,2,8,5,11,12,4,15,
13,8,11,5,6,15,0,3,4,7,2,12,1,10,14,9,
10,6,9,0,12,11,7,13,15,1,3,14,5,2,8,4,
3,15,0,6,10,1,13,8,9,4,5,11,12,7,2,14
	];
	let s5=[
2,12,4,1,7,10,11,6,8,5,3,15,13,0,14,9,
14,11,2,12,4,7,13,1,5,0,15,10,3,9,8,6,
4,2,1,11,10,13,7,8,15,9,12,5,6,3,0,14,
11,8,12,7,1,14,2,13,6,15,0,9,10,4,5,3
	];
	let s6=[
12,1,10,15,9,2,6,8,0,13,3,4,14,7,5,11,
10,15,4,2,7,12,9,5,6,1,13,14,0,11,3,8,
9,14,15,5,2,8,12,3,7,0,4,10,1,13,11,6,
4,3,2,12,9,5,15,10,11,14,1,7,6,0,8,13
	];
	let s7=[
4,11,2,14,15,0,8,13,3,12,9,7,5,10,6,1,
13,0,11,7,4,9,1,10,14,3,5,12,2,15,8,6,
1,4,11,13,12,3,7,14,10,15,6,8,0,5,9,2,
6,11,13,8,1,4,10,7,9,5,0,15,14,2,3,12
	];
	let s8=[
13,2,8,4,6,15,11,1,10,9,3,14,5,0,12,7,
1,15,13,8,10,3,7,4,12,5,6,11,0,14,9,2,
7,11,4,1,9,12,14,2,0,6,10,13,15,3,5,8,
2,1,14,7,4,10,8,13,15,12,9,0,3,5,6,11
	];
	let ss=[s1,s2,s3,s4,s5,s6,s7,s8];

	let toBits=function(v){
		let rtv=[];
		for(let x=0;x<v.length;x++) for(let z=8;z--;) rtv.push((v[x]>>z)&1);
		return rtv;
	},toBytes=function(v){
		let rtv=[];
		for(let x=0;x<v.length;x+=8){
			let t=0;
			for(let z=0;z<8;z++){
				let it=x+z;
				t=(t<<1)|(it<v.length?v[it]:0);
			}
			rtv.push(t);
		}
		return rtv;
	},xor=function(L,R){
		let rtv=[],minLen=Math.min(L.length,R.length);
		for(let x=0;x<minLen;x++) rtv.push(L[x]^R[x]);
		return rtv;
	},desKeyRotate=function(v){
		let b=toBits(v);
		let tmpL=b.shift(); b.push(b[27]); b[27]=tmpL;
		return toBytes(b);
	},mapping=function(mp,v){
		let rtv=[],b=toBits(v),newb=[];
		for(let x=0;x<mp.length;x++) newb.push(b[mp[x]-1]);
		return toBytes(newb);
	},sb=function(v){
		let rtv=[],b=toBits(v),tmpc=0;
		for(let x=0;x<ss.length;x++){
			let _=x*6;
			let it=(b[_]<<1)|b[_+5]; it<<=4; for(let z=4;z--;) it|=b[_+4-z]<<z;
			tmpc=(tmpc<<4)|ss[x][it];
			if(x&1){ rtv.push(tmpc); tmpc=0; }
		}
		return rtv;
	},parseBytes=function(s){
		let rtv=[],numsU="0123456789ABCDEF",numsL="0123456789abcdef",mp=[]; mp.length=256;
		for(let x=0;x<numsU.length;x++) mp[numsU.charCodeAt(x)]=x;
		for(let x=0;x<numsL.length;x++) mp[numsL.charCodeAt(x)]=x;
		let x=0;
		for(;x<s.length;x+=2){
			if(x&1) continue;
			let t1=mp[s.charCodeAt(x)],t2=mp[s.charCodeAt(x+1)];
			if(t1==undefined || t2==undefined) console.error("non-exist char");
			rtv.push((t1<<4)|t2);
		}
		if(x&1) console.error("not a hex string");
		return rtv;
	},sep32b=function(v){
		let rtv=[[],[]];
		for(let x=0;x<4;x++){
			rtv[0].push(v[x]);
			rtv[1].push(v[x+4]);
		}
		return rtv;
	},com=function(L,R){return [].concat(L).concat(R);},exchange32b=function(v){
		let tmp=sep32b(v);
		return com(tmp[1],tmp[0]);
	},desSubkeys=function(k){
		let rtv=[];
		let tmpkey=mapping(map_pc1,k);
		for(let x=0;x<16;x++){
			for(let z=map_shift[x];z--;) tmpkey=desKeyRotate(tmpkey);
			rtv.push(mapping(map_pc2,tmpkey));
		}
		return rtv;
	},des=function core(k,Bs,enc=false){
		if(enc) enc=1;
		if(core.subkeys==undefined) core.subkeys=desSubkeys(k);
		let rtv=[],order=[]; for(let x=16;x--;) order[x]=15*enc+x*(1-(enc<<1));
		for(let g=0;g<Bs.length;g+=8){
			let c=[]; c.length=8;
			for(let x=8;x--;){
				let it=g+x;
				c[x]=it<Bs.length?Bs[it]:0;
			}
			c=mapping(map_ip,c);
			let aaaa=sep32b(c);
			{ let tmp=aaaa[0]; aaaa[0]=aaaa[1]; aaaa[1]=tmp; }
			for(let x=16;x--;){
				console.log(core.subkeys[order[x]]);
				aaaa[1]=xor(mapping(map_p,sb(xor(mapping(map_e,aaaa[0]),core.subkeys[order[x]]))),aaaa[1]);
				{ let tmp=aaaa[0]; aaaa[0]=aaaa[1]; aaaa[1]=tmp; }
			}
			rtv=com(rtv,mapping(map_fp,com(aaaa[0],aaaa[1])));
		}
		return rtv;
	},desDecrypt=function(k,Bs){return des(k,Bs);},desEncrypt=function(k,Bs){return des(k,Bs,1);};
	let key=[]; for(let x=0;x<8;x++) key.push(s.charCodeAt(x));
	let res=desDecrypt(key,parseBytes(s.slice(8))),rtv="";
	for(let x=0;x<res.length;x++){ if(res[x]==0) break; rtv+=String.fromCharCode(res[x]); }
	return rtv;
};
let getGameAccountLoginInfo=function(query_serial,svcCode,svcRegion,accName,accSerial){
	jurl(hostAt+"beanfun_block/game_zone/game_start_step2.aspx?service_code="+svcCode+"&service_region="+svcRegion+"&sotp="+accSerial,"GET","",function(txt){
		if(query_serial!=infoQSerial){ console.log("conflict: info"); return; }
		let fail=0,SN="",WebToken="",CreateTime="";
		{
			let re=/GetResultByLongPolling&key=(.*)\"/g;
			let m=txt.match(re);
			if(m==null){ console.log("fail: SN"); fail+=1; }
			else{
				SN=m[0].replace(re,"$1");
			}
		}
		{
			let re=/&&&&WebToken=([0-9A-Fa-f]+)((&&&&)|$)/g;
			let m=txt.match(re);
			if(m==null){ console.log("fail: WebToken"); fail+=1; }
			else{
				WebToken=m[0].replace(re,"$1");
			}
		}
		{
			let re=/CreateTime([\s\t]*):([\s\t]*)(\"([0-9\s-:]+)\"|\'([0-9\s-:]+)\')/g;
			let m=txt.match(re);
			if(m==null){ console.log("fail: CreateTime"); fail+=1; }
			else{
				CreateTime=m[0].replace(re,"$3").replace(/\'/g,"").replace(/\"/g,"");
				CreateTime=CreateTime.replace(/\s/g,"%20");
			}
		}
		if(fail!=0) console.log(SN,WebToken,m_strSecretCode,CreateTime);
		else jurl(hostAt+"beanfun_block/generic_handlers/get_webstart_otp.ashx"+
				"?SN="+SN+
				"&WebToken="+ WebToken +
				"&SecretCode="+ m_strSecretCode +
				"&ppppp=1F552AEAFF976018F942B13690C990F60ED01510DDF89165F1658CCE7BC21DBA"+
				"&ServiceCode="+ svcCode +
				"&ServiceRegion="+ svcRegion +
				"&ServiceAccount="+ accName +
				"&CreateTime="+ CreateTime ,
			"GET","",function(txt){
				if(txt.slice(0,1)!="1") console.log(txt);
				else{
					otp.ra(1).ac(q.ce("div").at("calculating ..."));
					let otpCode=desDecrypt(txt.slice(2));
					otp.ra(1).ac(q.ce("div").at(otpCode));
				}
		});
	});

};
let loadAccoutns=function loadAccoutns(query_serial,gameId){
	acc.ra(1);
	acc.ac(q.ce("div").at("loading ..."));
	jurl(hostAt+"beanfun_block/game_zone/game_start.aspx?service_code_and_region="+gameId,"GET","",function(txt){
		if(query_serial!=accQSerial){ console.log("conflict: accs"); return; }
		acc.ra(1);
		let svc=gameId.split("_");
		let rtvdom=new DOMParser().parseFromString(txt,"text/html");
		let arr=rtvdom.querySelectorAll("#divServiceAccountList>ul>li>div.Account");
		for(let x=0;x<arr.length;x++){
			let r=arr[x],a=q.ce("div").sa("accName",r.ga("id")).sa("uid",r.ga("sn")).ac(
				q.ce("div").at(r.ga("name"))
			);
			a.onclick=function(){getGameAccountLoginInfo(infoQSerial+=1,svc[0],svc[1],r.ga("id"),r.ga("sn"));};
			acc.ac(a);
		}
	});
};
let loadGames=function loadGames(){
	game.ra(1);
	game.ac(q.ce("div").at("loading ..."));
	jurl(hostAt+"generic_handlers/gamezone.ashx","POST",(function(){
		let rtv=new FormData();
		rtv.append("strFunction","getOpenedServices");
		rtv.append("webtoken","1");
		return rtv;
	})(),function(txt){
		game.ra(1);
		let arr=JSON.parse(txt)["strServices"].split(",");
		for(let x=arr.length;x--;){
			let div=q.ce("div").at(arr[x]);
			div.onclick=function(){loadAccoutns(accQSerial+=1,arr[x]);};
			game.ac(div);
		}
	});
};

q.ce=function(h){return d.createElement(h);};
q.ge=function(i){return d.getElementById(i);};
Array.prototype.back=function(){return this.length==0?undefined:this[this.length-1];};
HTMLElement.prototype.ac=function(c){this.appendChild(c); return this;};
HTMLElement.prototype.ga=function(a){return this.getAttribute(a);};
HTMLElement.prototype.sa=function(a,v){this.setAttribute(a,v);return this;};
HTMLElement.prototype.at=function(t){this.ac(d.createTextNode(t));return this;};
HTMLElement.prototype.ra=function(n){let arr=this.childNodes;while(arr.length!=0&&arr.length>n)this.removeChild(arr[arr.length-1]);return this;};



// main
clearCurrent();
if(typeof(m_strSecretCode)==typeof(undefined)) document.body.appendChild((function(){
	let s=document.createElement("script").sa("type","text/javascript").sa("src","https://tw.newlogin.beanfun.com/generic_handlers/get_cookies.ashx");
	s.onload=function(){
		console.log("session key loaded");
		//console.log(m_strSecretCode);
		let errMsg=q.ge("errMsg");
		if(errMsg!=null) errMsg.parentNode.removeChild(errMsg);
		genBlock();
		loadGames();
	};
	s.onerror=function(){
		let errMsg=q.ge("errMsg");
		if(errMsg==null) d.body.ac(errMsg=q.ce("div"));
		errMsg.ac(q.ce("div").sa("id","error").at("error: unable to get 'SecretCode'"));
	};
	return s;
})());


})();
