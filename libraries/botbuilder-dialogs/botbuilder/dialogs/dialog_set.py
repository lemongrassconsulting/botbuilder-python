# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .dialog import Dialog
from .dialog_state import DialogState
from .dialog_turn_result import DialogTurnResult
from .dialog_reason import DialogReason
from .dialog_context import DialogContext
from botbuilder.core import (
                            TurnContext,
                            BotAssert,
                            StatePropertyAccessor
                            )
from typing import Dict


class DialogSet():

    def __init__(self, dialog_state: StatePropertyAccessor):
        if dialog_state is None:
            raise TypeError('DialogSet(): dialog_state cannot be None.')
        self._dialog_state = dialog_state
        # self.__telemetry_client = NullBotTelemetryClient.Instance;

        self._dialogs: Dict[str, object] = {}

    
    
    async def add(self, dialog: Dialog):
        """
        Adds a new dialog to the set and returns the added dialog.
        :param dialog: The dialog to add.
        """
        if dialog is None or not isinstance(dialog, Dialog):
            raise TypeError('DialogSet.add(): dialog cannot be None and must be a Dialog or derived class.')

        if dialog.id in self._dialogs:
            raise TypeError("DialogSet.add(): A dialog with an id of '%s' already added." % dialog.id)

        # dialog.telemetry_client = this._telemetry_client;
        self._dialogs[dialog.id] = dialog

        return self

    async def create_context(self, turn_context: TurnContext) -> DialogContext:
        BotAssert.context_not_null(turn_context)
        
        if not self._dialog_state:
            raise RuntimeError("DialogSet.CreateContextAsync(): DialogSet created with a null IStatePropertyAccessor.")
        
        state = await self._dialog_state.get(turn_context, lambda: DialogState())

        return DialogContext(self, turn_context, state)

    async def find(self, dialog_id: str) -> Dialog:
        """
        Finds a dialog that was previously added to the set using add(dialog)
        :param dialog_id: ID of the dialog/prompt to look up.
        :return: The dialog if found, otherwise null.
        """
        if (not dialog_id):
            raise TypeError('DialogContext.find(): dialog_id cannot be None.');

        if dialog_id in self._dialogs:
            return self._dialogs[dialog_id]

        return None

