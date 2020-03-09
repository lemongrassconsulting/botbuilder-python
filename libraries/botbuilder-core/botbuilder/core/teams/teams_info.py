# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import List, Tuple
from botbuilder.schema import ConversationParameters, ConversationReference
from botbuilder.core.turn_context import Activity, TurnContext
from botbuilder.schema.teams import (
    ChannelInfo,
    TeamDetails,
    TeamsChannelData,
    TeamsChannelAccount,
)
from botframework.connector.aio import ConnectorClient
from botframework.connector.teams.teams_connector_client import TeamsConnectorClient


class TeamsInfo:
    @staticmethod
    async def send_message_to_teams_channel(
        turn_context: TurnContext, activity: Activity, teams_channel_id: str
    ) -> Tuple[ConversationReference, str]:
        if not turn_context:
            raise ValueError("The turn_context cannot be None")
        if not turn_context.activity:
            raise ValueError("The turn_context.activity cannot be None")
        if not teams_channel_id:
            raise ValueError("The teams_channel_id cannot be None or empty")

        old_ref = TurnContext.get_conversation_reference(turn_context.activity)
        conversation_parameters = ConversationParameters(
            is_group=True,
            channel_data={"channel": {"id": teams_channel_id}},
            activity=activity,
        )

        result = await turn_context.adapter.create_conversation(
            old_ref, TeamsInfo._create_conversation_callback, conversation_parameters
        )
        return (result[0], result[1])

    @staticmethod
    async def _create_conversation_callback(
        new_turn_context,
    ) -> Tuple[ConversationReference, str]:
        new_activity_id = new_turn_context.activity.id
        conversation_reference = TurnContext.get_conversation_reference(
            new_turn_context.activity
        )
        return (conversation_reference, new_activity_id)

    @staticmethod
    async def get_team_details(
        turn_context: TurnContext, team_id: str = ""
    ) -> TeamDetails:
        if not team_id:
            team_id = TeamsInfo.get_team_id(turn_context)

        if not team_id:
            raise TypeError(
                "TeamsInfo.get_team_details: method is only valid within the scope of MS Teams Team."
            )

        teams_connector = await TeamsInfo.get_teams_connector_client(turn_context)
        return teams_connector.teams.get_team_details(team_id)

    @staticmethod
    async def get_team_channels(
        turn_context: TurnContext, team_id: str = ""
    ) -> List[ChannelInfo]:
        if not team_id:
            team_id = TeamsInfo.get_team_id(turn_context)

        if not team_id:
            raise TypeError(
                "TeamsInfo.get_team_channels: method is only valid within the scope of MS Teams Team."
            )

        teams_connector = await TeamsInfo.get_teams_connector_client(turn_context)
        return teams_connector.teams.get_teams_channels(team_id).conversations

    @staticmethod
    async def get_team_members(turn_context: TurnContext, team_id: str = ""):
        if not team_id:
            team_id = TeamsInfo.get_team_id(turn_context)

        if not team_id:
            raise TypeError(
                "TeamsInfo.get_team_members: method is only valid within the scope of MS Teams Team."
            )

        connector_client = await TeamsInfo._get_connector_client(turn_context)
        return await TeamsInfo._get_members(
            connector_client, turn_context.activity.conversation.id,
        )

    @staticmethod
    async def get_members(turn_context: TurnContext) -> List[TeamsChannelAccount]:
        team_id = TeamsInfo.get_team_id(turn_context)
        if not team_id:
            conversation_id = turn_context.activity.conversation.id
            connector_client = await TeamsInfo._get_connector_client(turn_context)
            return await TeamsInfo._get_members(connector_client, conversation_id)

        return await TeamsInfo.get_team_members(turn_context, team_id)

    @staticmethod
    async def get_teams_connector_client(
        turn_context: TurnContext,
    ) -> TeamsConnectorClient:
        # A normal connector client is retrieved in order to use the credentials
        # while creating a TeamsConnectorClient below
        connector_client = await TeamsInfo._get_connector_client(turn_context)

        return TeamsConnectorClient(
            connector_client.config.credentials, turn_context.activity.service_url,
        )

    @staticmethod
    def get_team_id(turn_context: TurnContext):
        channel_data = TeamsChannelData(**turn_context.activity.channel_data)
        if channel_data.team:
            return channel_data.team["id"]
        return ""

    @staticmethod
    async def _get_connector_client(turn_context: TurnContext) -> ConnectorClient:
        return await turn_context.adapter.create_connector_client(
            turn_context.activity.service_url
        )

    @staticmethod
    async def _get_members(
        connector_client: ConnectorClient, conversation_id: str
    ) -> List[TeamsChannelAccount]:
        if connector_client is None:
            raise TypeError("TeamsInfo._get_members.connector_client: cannot be None.")

        if not conversation_id:
            raise TypeError("TeamsInfo._get_members.conversation_id: cannot be empty.")

        teams_members = []
        members = await connector_client.conversations.get_conversation_members(
            conversation_id
        )

        for member in members:
            teams_members.append(
                TeamsChannelAccount().deserialize(
                    dict(member.serialize(), **member.additional_properties)
                )
            )

        return teams_members
