#ifndef VPN_CORE_H
#define VPN_CORE_H

#ifdef _WIN32
    #define VPN_API __declspec(dllexport)
#else
    #define VPN_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Kiểm tra độ trễ (Latency/Ping) tới IP chỉ định.
 * @param ip Đia chỉ IP hoặc Domain cần ping.
 * @return Độ trễ tính bằng ms (ms), trả về -1 nếu Timeout hoặc lỗi.
 */
VPN_API int CheckLatency(const char* ip);

#ifdef __cplusplus
}
#endif

#endif // VPN_CORE_H