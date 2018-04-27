// current version not completed
// still need to install web plugin
// DES decryption is not implemented yet

// beanfun login
// need to paste on console

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
let rt,svc,game,acc; // DOM
let accQSerial=0,infoQSerial=0; // prevent conflict
let genBlock=function genBlock(){
	rt=q.ce("div").sa("id","root").sa("class","maxToParent");
	rt.ac( q.ce("div").sa("id","otp1").sa("class","otp").ac(q.ce("div").at("otp:")) );
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
			console.log(txt);
	});
});

};
let loadAccoutns=function loadAccoutns(query_serial,gameId){
	acc.ra(1);
	acc.ac(q.ce("div").at("loading ..."));
	jurl(hostAt+"beanfun_block/game_zone/game_start.aspx?service_code_and_region="+gameId,"GET","",function(txt){
		if(query_serial!=accQSerial){ console.log("conflict: accs"); return; }
		console.log(txt);
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
		//console.log(txt);
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
