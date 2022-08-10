#include <curl/curl.h>
#include <fstream>
#include "json.hpp"
#include <iostream>
#include <sstream>

using json = nlohmann::json;

/*
 * \" -> "
 * \\" -> \"
 * \' -> '
 */


int main(int argc, char* argv[]){
	std::fstream f("read");
	std::stringstream buffer;
	buffer << f.rdbuf();

	std::string str = buffer.str();

	while(true){
		std::size_t pos = str.find("\\\"");
		if(pos == std::string::npos) break;

		str.replace(pos, str.size(), "\"");
	}
	while(true){
		std::size_t pos = str.find("\\\\\"");
		if(pos == std::string::npos) break;

		str.replace(pos, str.size(), "\\\"");
	}
	while(true){
		std::size_t pos = str.find("\\'");
		if(pos == std::string::npos) break;

		str.replace(pos, str.size(), "'");
	}


	json data = json::parse(str);

	std::cout << data << "\n";
}
