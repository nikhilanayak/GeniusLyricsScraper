import fetch from "node-fetch";
import HTMLParser from "fast-html-parser";
import fs from "fs";

const JSON_PREFIX = "window.__PRELOADED_STATE__ =";

function processLyricsHTML(HTMLString){
	if(HTMLString == null) return null;

	const dom = HTMLParser.parse(HTMLString);
	return dom.text;

}

function mapKVArray(list){
	//console.log(list);
	if(list == null) return null;

	const out = {};
	for(let item in list){
		item = list[item];

		if(item.values != null) item.value = item.values;
		if(item.name != null) item.key = item.name

		out[item.key] = item.value;
	}
	//console.log(out);
	return out;
}


async function scrape(id, try_=5){
	if(try_==0) return null;

	//console.log("started", id);
	const url = `https://genius.com/songs/${id}`;

	let res;

	try{
		res = await fetch(url);
	}
	catch(err){
		return await scrape(id, try_=try_-1);
	}
	
	if(res.status != 200){
		if(res.status != 404){
			return await scrape(id, try_=try_-1);
		}
	}

	const text = await res.text();

	const lines = text.split("\n");

	for(let line of lines){
		line = line.trim();
		if(!line.startsWith(JSON_PREFIX)){
			continue;
		}

		line = line.slice(JSON_PREFIX.length, line.length);
		line = "return " + line;

		console.log(line);
		process.exit(0);

		const data = (new Function(line))();
		return data;

		const dfp = {...mapKVArray(data?.songPage?.trackingData), ...mapKVArray(data?.songPage?.dfpKv)}

		const pageType = data?.songPage?.pageType;
		const lyrics = processLyricsHTML(data?.songPage?.lyricsData?.body?.html);
		const title = {
			name: dfp?.Title,
			id: dfp?.["Song ID"]
		};
		const artist = {
			name: dfp?.["Primary Artist"],
			id: dfp?.["Primary Artist ID"]	
		};
		const genre = dfp?.Tag;
		const isMusic = dfp?.["Music?"];
		const releaseDate = dfp?.["Release Date"];
		const language = dfp?.["Lyrics Language"];
		const topic = dfp?.topic?.[0];
		const url = data?.songPage?.path;

		console.log("\t", id);
		return {
			id: id,
			pageType: pageType,
			lyrics: lyrics,
			title: title,
			artist: artist,
			genre: genre,
			isMusic: isMusic,
			releaseDate: releaseDate,
			language: language,
			topic: topic,
			url: url
		};
		
	}

	return await scrape(id, try_=try_-1);
}

const BATCH_SIZE = 1024;
let i = 0;

while(true){
	let start = i * BATCH_SIZE;
	let end = start + BATCH_SIZE;

	let promises = [];
	for(let id = start; id < end; id++){
		promises.push(scrape(id));
	}


	let data = [];

	let done = 0;
	for(let p of promises){
		data.push(await p);
		done += 1;
		process.stdout.write(`${i}: ${done}\r`);
	}
	console.log();



	//const data = await Promise.all(promises);
	

	fs.writeFile(`data/${i}.json`, JSON.stringify(data), (err => {
		if(err){
			console.log(err);
		}
	}));
	console.log(i);
	i++;
}


/*const res = await scrape(1);

console.log(JSON.stringify(res));*/
