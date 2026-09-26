#include "../include/vpn_core.h"
#include <iostream>
#include <cstdlib>
#include <chrono>
#include <string>

VPN_API int CheckLatency(const char* ip) {
    if (!ip) return -1;

    std::string command;
#ifdef _WIN32
    command = "ping -n 1 -w 1000 ";
    command += ip;
    command += " > nul";
#else
    command = "ping -c 1 -W 1 ";
    command += ip;
    command += " > /dev/null 2>&1";
#endif

    auto start = std::chrono::high_resolution_clock::now();
    int result = std::system(command.c_str());
    auto end = std::chrono::high_resolution_clock::now();

    if (result == 0) {
        std::chrono::duration<double, std::milli> elapsed = end - start;
        return static_cast<int>(elapsed.count());
    }

    return -1; // Timeout hoặc lỗi
}