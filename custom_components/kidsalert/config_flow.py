"""Config flow for KidsAlert."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import KidsAlertApi, KidsAlertApiError
from .const import (
    CONF_DANGER_HOURS,
    CONF_LANGUAGE,
    CONF_SCAN_INTERVAL,
    DEFAULT_DANGER_HOURS,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LANGUAGES,
    MAX_DANGER_HOURS,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


class KidsAlertConfigFlow(ConfigFlow, domain=DOMAIN):
    """One entry per alert language."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            language = user_input[CONF_LANGUAGE]
            await self.async_set_unique_id(language)
            self._abort_if_unique_id_configured()
            try:
                await KidsAlertApi(async_get_clientsession(self.hass), language).async_get_alerts()
            except KidsAlertApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"KidsAlert ({language.upper()})",
                    data={CONF_LANGUAGE: language},
                )

        ha_language = self.hass.config.language
        default_language = ha_language if ha_language in LANGUAGES else DEFAULT_LANGUAGE
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LANGUAGE, default=default_language): SelectSelector(
                        SelectSelectorConfig(
                            options=LANGUAGES,
                            mode=SelectSelectorMode.LIST,
                            translation_key=CONF_LANGUAGE,
                        )
                    )
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return KidsAlertOptionsFlow()


class KidsAlertOptionsFlow(OptionsFlow):
    """Polling interval and danger window."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={key: int(value) for key, value in user_input.items()}
            )

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=1,
                            unit_of_measurement="min",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_DANGER_HOURS,
                        default=options.get(CONF_DANGER_HOURS, DEFAULT_DANGER_HOURS),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=MAX_DANGER_HOURS,
                            step=1,
                            unit_of_measurement="h",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
