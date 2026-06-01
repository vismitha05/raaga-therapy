# eeg/neiry_adapter.py
import asyncio
import numpy as np
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter

BOARD_ID = BoardIds.NEIRY_BOARD   # 36

class NeiryAdapter:
    def __init__(self):
        BoardShim.enable_dev_board_logger()
        params = BrainFlowInputParams()
        # For BLE: params.serial_port = ""  (auto-discover)
        # For USB: params.serial_port = "/dev/ttyUSB0" or "COM3"
        self.board = BoardShim(BOARD_ID, params)
        self.eeg_channels = BoardShim.get_eeg_channels(BOARD_ID)
        self.sample_rate = BoardShim.get_sampling_rate(BOARD_ID)  # 250 Hz

    def start(self):
        self.board.prepare_session()
        self.board.start_stream(450000)   # 45 s ring buffer

    def get_current_data(self, num_samples: int) -> np.ndarray:
        """Returns shape (n_channels, num_samples). Non-blocking."""
        return self.board.get_current_board_data(num_samples)[self.eeg_channels, :]

    def stop(self):
        if self.board.is_prepared():
            self.board.stop_stream()
            self.board.release_session()