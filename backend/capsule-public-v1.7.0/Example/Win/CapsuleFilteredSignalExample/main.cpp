#include <chrono>
#include <iostream>
#include <thread>
#include <winsock2.h>

#include "ExampleUtils.hpp"
#include "Capsule/CClient.h"
#include "Capsule/CDevice.h"
#include "Capsule/CSession.h"

#pragma comment(lib, "ws2_32.lib")

using namespace std::chrono_literals;

// ---------------- SOCKET ----------------
SOCKET sock;

void initSocket() {
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);

    sockaddr_in server;
    server.sin_addr.s_addr = inet_addr("127.0.0.1");
    server.sin_family = AF_INET;
    server.sin_port = htons(5001);

    while (true) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock == INVALID_SOCKET) {
            std::cerr << "[C++] Failed to create socket, retrying...\n";
            std::this_thread::sleep_for(1s);
            continue;
        }

        int rc = connect(sock, (struct sockaddr*)&server, sizeof(server));
        if (rc == 0) {
            std::cout << "[C++] Connected to Python backend\n";
            break;
        }

        std::cerr << "[C++] Python backend not ready on 127.0.0.1:5001, retrying...\n";
        closesocket(sock);
        std::this_thread::sleep_for(1s);
    }
}

// ---------------- CAPSULE OBJECTS ----------------
clCClient client = nullptr;
clCSession session = nullptr;
clCDeviceLocator locator = nullptr;
clCDevice device = nullptr;

uint32_t s_time = 0;
uint32_t deviceConnectionTime = 0;

bool bipolarMode = false;
bool clientStopRequested = false;
bool clientDisconnecting = false;
bool sessionStartRequested = false;
bool deviceReconnectRequested = false;
uint32_t lastReconnectAttemptTime = 0;
bool deviceRescanRequested = false;
uint32_t lastRescanAttemptTime = 0;

// ---------------- EEG CALLBACK ----------------
void onSessionEEGData(clCSession, clCEEGTimedData eegData) {

    std::cout << "[C++] EEG data received\n";

    int samples = clCEEGTimedData_GetSamplesCount(eegData);
    int channels = clCEEGTimedData_GetChannelsCount(eegData);

    for (int i = 0; i < samples; i++) {

        std::string line = "";

        for (int j = 0; j < channels; j++) {
            float val = clCEEGTimedData_GetValue(eegData, j, i);

            line += std::to_string(val);
            if (j != channels - 1)
                line += ",";
        }

        line += "\n";

        send(sock, line.c_str(), line.size(), 0);
    }
}

// ---------------- SESSION CALLBACKS ----------------
void onSessionStarted(clCSession) {
    std::cout << "[C++] Session started\n";
    clCDevice_SwitchMode(device, clC_DM_Signal);
}

void onConnectionStateChanged(clCDevice, clCDeviceConnectionState state) {
    std::cout << "[C++] Device state changed: " << (int)state << "\n";

    if (state == clC_SE_Connected) {
        std::cout << "[C++] Device connected\n";
        deviceConnectionTime = s_time;
        sessionStartRequested = false;
        deviceReconnectRequested = false;
        deviceRescanRequested = false;
        return;
    }

    if (state == clC_SE_Disconnected) {
        std::cout << "[C++] Device disconnected\n";
        session = nullptr;
        deviceConnectionTime = 0;
        sessionStartRequested = false;
        deviceReconnectRequested = true;
        return;
    }

    if (state == clC_SE_UnsupportedConnection) {
        std::cout << "[C++] Device connection unsupported (state=2). Will rescan devices...\n";
        session = nullptr;
        deviceConnectionTime = 0;
        sessionStartRequested = false;
        deviceReconnectRequested = false;
        deviceRescanRequested = true;
        return;
    }
}

void onDeviceList(clCDeviceLocator locator, clCDeviceInfoList devices, clCDeviceLocatorFailReason error) {

    if (clCDeviceInfoList_GetCount(devices) == 0) {
        std::cerr << "[C++] No devices found\n";
        clientStopRequested = true;
        return;
    }

    clCDeviceInfo info = clCDeviceInfoList_GetDeviceInfo(devices, 0);
    clCString deviceID = clCDeviceInfo_GetID(info);

    device = clCDeviceLocator_CreateDevice(locator, clCString_CStr(deviceID));
    clCString_Free(deviceID);

    auto event = clCDevice_GetOnConnectionStateChangedEvent(device);
    clCDeviceDelegateConnectionState_Set(event, onConnectionStateChanged);

    std::cout << "[C++] device found: " << clCDeviceInfoList_GetCount(devices) << std::endl;

    clCDevice_Connect(device);
}

void onConnected(clCClient client) {
    std::cout << "[C++] Connected to Capsule\n";

    locator = clCClient_ChooseDeviceType(client, clC_DT_NeiryBand);

    auto event = clCDeviceLocator_GetOnDevicesEvent(locator);
    clCDeviceLocatorDelegateDeviceInfoList_Set(event, onDeviceList);

    clCDeviceLocator_RequestDevices(locator, 15);
}

void onDisconnected(clCClient, clCDisconnectReason reason) {
    std::cout << "[C++] Disconnected: " << (int)reason << std::endl;
    clientStopRequested = true;
}

// ---------------- MAIN LOOP ----------------
void ClientLoop() {

    while (client) {

        clCClient_Update(client);
        std::this_thread::sleep_for(50ms);
        s_time += 50;

        if (deviceConnectionTime && s_time == deviceConnectionTime + 2000 && !session) {

            auto error = clC_Error_OK;

            session = clCClient_CreateSessionWithMonopolarChannelsWithError(client, device, &error);

            auto eegEvent = clCSession_GetOnSessionEEGDataEvent(session);
            clCSessionDelegateSessionEEGData_Set(eegEvent, onSessionEEGData);

            clCSession_Start(session);
        }
    }
}

// ---------------- MAIN ----------------
int main(int argc, char* argv[]) {

    std::cout << "[C++] Starting EEG stream...\n";

    initSocket();

    client = clCClient_CreateWithName("EEGClient");

    auto onConn = clCClient_GetOnConnectedEvent(client);
    clCClientDelegate_Set(onConn, onConnected);

    auto onDisc = clCClient_GetOnDisconnectedEvent(client);
    clCClientDelegateDisconnectReason_Set(onDisc, onDisconnected);

    clCClient_Connect(client, "inproc://capsule");

    std::cout << "[C++] Waiting for EEG data... Press q to quit\n";

    while (true) {
        clCClient_Update(client);
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        s_time += 50;

        if (deviceReconnectRequested && device &&
            s_time >= lastReconnectAttemptTime + 2000) {
            lastReconnectAttemptTime = s_time;
            std::cout << "[C++] Attempting device reconnect...\n";
            clCDevice_Connect(device);
        }

        if (deviceRescanRequested && locator &&
            s_time >= lastRescanAttemptTime + 3000) {
            lastRescanAttemptTime = s_time;
            std::cout << "[C++] Requesting device list again...\n";
            clCDeviceLocator_RequestDevices(locator, 15);
        }

        if (deviceConnectionTime && !session && !sessionStartRequested &&
            s_time >= deviceConnectionTime + 2000) {

            sessionStartRequested = true;
            auto error = clC_Error_OK;
            session = clCClient_CreateSessionWithMonopolarChannelsWithError(client, device, &error);

            if (!session || error != clC_Error_OK) {
                std::cerr << "[C++] Failed to create session. error=" << (int)error << "\n";
                session = nullptr;
                sessionStartRequested = false;
            }
            else {
                std::cout << "[C++] Session created\n";

                auto startedEvent = clCSession_GetOnSessionStartedEvent(session);
                clCSessionDelegate_Set(startedEvent, onSessionStarted);

                auto eegEvent = clCSession_GetOnSessionEEGDataEvent(session);
                clCSessionDelegateSessionEEGData_Set(eegEvent, onSessionEEGData);

                std::cout << "[C++] Starting session...\n";
                clCSession_Start(session);
                clCDevice_SwitchMode(device, clC_DM_Signal);
            }
        }

        if (GetAsyncKeyState('Q')) {
            break;
        }
    }

    return 0;
}
