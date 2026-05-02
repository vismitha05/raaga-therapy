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

    sock = socket(AF_INET, SOCK_STREAM, 0);

    sockaddr_in server;
    server.sin_addr.s_addr = inet_addr("127.0.0.1");
    server.sin_family = AF_INET;
    server.sin_port = htons(5000);

    connect(sock, (struct sockaddr*)&server, sizeof(server));

    std::cout << "[C++] Connected to Python backend\n";
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

// ---------------- EEG CALLBACK ----------------
void onSessionEEGData(clCSession, clCEEGTimedData eegData) {

    std::cout << "[C++] Received EEG data\n";

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
    if (state != clC_SE_Connected) {
        std::cout << "[C++] Device disconnected\n";
        return;
    }

    std::cout << "[C++] Device connected\n";
    deviceConnectionTime = s_time;
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
    exit(0);
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

        if (GetAsyncKeyState('Q')) {
            break;
        }
    }

    return 0;
}