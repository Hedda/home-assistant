"""The tests for the MQTT JSON light platform.

Configuration with RGB, brightness, color temp, effect, white value and XY:

light:
  platform: mqtt_json
  name: mqtt_json_light_1
  state_topic: "home/rgb1"
  command_topic: "home/rgb1/set"
  brightness: true
  color_temp: true
  effect: true
  rgb: true
  white_value: true
  xy: true

Configuration with RGB, brightness, color temp, effect, white value:

light:
  platform: mqtt_json
  name: mqtt_json_light_1
  state_topic: "home/rgb1"
  command_topic: "home/rgb1/set"
  brightness: true
  color_temp: true
  effect: true
  rgb: true
  white_value: true

Configuration with RGB, brightness, color temp and effect:

light:
  platform: mqtt_json
  name: mqtt_json_light_1
  state_topic: "home/rgb1"
  command_topic: "home/rgb1/set"
  brightness: true
  color_temp: true
  effect: true
  rgb: true

Configuration with RGB, brightness and color temp:

light:
  platform: mqtt_json
  name: mqtt_json_light_1
  state_topic: "home/rgb1"
  command_topic: "home/rgb1/set"
  brightness: true
  rgb: true
  color_temp: true

Configuration with RGB, brightness:

light:
  platform: mqtt_json
  name: mqtt_json_light_1
  state_topic: "home/rgb1"
  command_topic: "home/rgb1/set"
  brightness: true
  rgb: true

Config without RGB:

light:
  platform: mqtt_json
  name: mqtt_json_light_1
  state_topic: "home/rgb1"
  command_topic: "home/rgb1/set"
  brightness: true

Config without RGB and brightness:

light:
  platform: mqtt_json
  name: mqtt_json_light_1
  state_topic: "home/rgb1"
  command_topic: "home/rgb1/set"

Config with brightness and scale:

light:
  platform: mqtt_json
  name: test
  state_topic: "mqtt_json_light_1"
  command_topic: "mqtt_json_light_1/set"
  brightness: true
  brightness_scale: 99
"""

import json
import unittest
from unittest.mock import patch

from homeassistant.setup import setup_component
from homeassistant.const import (
    STATE_ON, STATE_OFF, STATE_UNAVAILABLE, ATTR_ASSUMED_STATE,
    ATTR_SUPPORTED_FEATURES)
import homeassistant.components.light as light
from homeassistant.components.mqtt.discovery import async_start
import homeassistant.core as ha

from tests.common import (
    get_test_home_assistant, mock_mqtt_component, fire_mqtt_message,
    assert_setup_component, mock_coro, async_fire_mqtt_message)
from tests.components.light import common


class TestLightMQTTJSON(unittest.TestCase):
    """Test the MQTT JSON light."""

    def setUp(self):  # pylint: disable=invalid-name
        """Set up things to be run when tests are started."""
        self.hass = get_test_home_assistant()
        self.mock_publish = mock_mqtt_component(self.hass)

    def tearDown(self):  # pylint: disable=invalid-name
        """Stop everything that was started."""
        self.hass.stop()

    def test_fail_setup_if_no_command_topic(self):
        """Test if setup fails with no command topic."""
        with assert_setup_component(0, light.DOMAIN):
            assert setup_component(self.hass, light.DOMAIN, {
                light.DOMAIN: {
                    'platform': 'mqtt_json',
                    'name': 'test',
                }
            })
        assert self.hass.states.get('light.test') is None

    def test_no_color_brightness_color_temp_white_val_if_no_topics(self):
        """Test for no RGB, brightness, color temp, effect, white val or XY."""
        assert setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {
                'platform': 'mqtt_json',
                'name': 'test',
                'state_topic': 'test_light_rgb',
                'command_topic': 'test_light_rgb/set',
            }
        })

        state = self.hass.states.get('light.test')
        assert STATE_OFF == state.state
        assert 40 == state.attributes.get(ATTR_SUPPORTED_FEATURES)
        assert state.attributes.get('rgb_color') is None
        assert state.attributes.get('brightness') is None
        assert state.attributes.get('color_temp') is None
        assert state.attributes.get('effect') is None
        assert state.attributes.get('white_value') is None
        assert state.attributes.get('xy_color') is None
        assert state.attributes.get('hs_color') is None

        fire_mqtt_message(self.hass, 'test_light_rgb', '{"state":"ON"}')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert state.attributes.get('rgb_color') is None
        assert state.attributes.get('brightness') is None
        assert state.attributes.get('color_temp') is None
        assert state.attributes.get('effect') is None
        assert state.attributes.get('white_value') is None
        assert state.attributes.get('xy_color') is None
        assert state.attributes.get('hs_color') is None

    def test_controlling_state_via_topic(self):
        """Test the controlling of the state via topic."""
        assert setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {
                'platform': 'mqtt_json',
                'name': 'test',
                'state_topic': 'test_light_rgb',
                'command_topic': 'test_light_rgb/set',
                'brightness': True,
                'color_temp': True,
                'effect': True,
                'rgb': True,
                'white_value': True,
                'xy': True,
                'hs': True,
                'qos': '0'
            }
        })

        state = self.hass.states.get('light.test')
        assert STATE_OFF == state.state
        assert 191 == state.attributes.get(ATTR_SUPPORTED_FEATURES)
        assert state.attributes.get('rgb_color') is None
        assert state.attributes.get('brightness') is None
        assert state.attributes.get('color_temp') is None
        assert state.attributes.get('effect') is None
        assert state.attributes.get('white_value') is None
        assert state.attributes.get('xy_color') is None
        assert state.attributes.get('hs_color') is None
        assert not state.attributes.get(ATTR_ASSUMED_STATE)

        # Turn on the light, full white
        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"color":{"r":255,"g":255,"b":255},'
                          '"brightness":255,'
                          '"color_temp":155,'
                          '"effect":"colorloop",'
                          '"white_value":150}')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert (255, 255, 255) == state.attributes.get('rgb_color')
        assert 255 == state.attributes.get('brightness')
        assert 155 == state.attributes.get('color_temp')
        assert 'colorloop' == state.attributes.get('effect')
        assert 150 == state.attributes.get('white_value')
        assert (0.323, 0.329) == state.attributes.get('xy_color')
        assert (0.0, 0.0) == state.attributes.get('hs_color')

        # Turn the light off
        fire_mqtt_message(self.hass, 'test_light_rgb', '{"state":"OFF"}')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_OFF == state.state

        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"brightness":100}')
        self.hass.block_till_done()

        light_state = self.hass.states.get('light.test')
        self.hass.block_till_done()
        assert 100 == \
            light_state.attributes['brightness']

        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"color":{"r":125,"g":125,"b":125}}')
        self.hass.block_till_done()

        light_state = self.hass.states.get('light.test')
        assert (255, 255, 255) == \
            light_state.attributes.get('rgb_color')

        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"color":{"x":0.135,"y":0.135}}')
        self.hass.block_till_done()

        light_state = self.hass.states.get('light.test')
        assert (0.141, 0.14) == \
            light_state.attributes.get('xy_color')

        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"color":{"h":180,"s":50}}')
        self.hass.block_till_done()

        light_state = self.hass.states.get('light.test')
        assert (180.0, 50.0) == \
            light_state.attributes.get('hs_color')

        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"color_temp":155}')
        self.hass.block_till_done()

        light_state = self.hass.states.get('light.test')
        assert 155 == light_state.attributes.get('color_temp')

        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"effect":"colorloop"}')
        self.hass.block_till_done()

        light_state = self.hass.states.get('light.test')
        assert 'colorloop' == light_state.attributes.get('effect')

        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"white_value":155}')
        self.hass.block_till_done()

        light_state = self.hass.states.get('light.test')
        assert 155 == light_state.attributes.get('white_value')

    def test_sending_mqtt_commands_and_optimistic(self):
        """Test the sending of command in optimistic mode."""
        fake_state = ha.State('light.test', 'on', {'brightness': 95,
                                                   'hs_color': [100, 100],
                                                   'effect': 'random',
                                                   'color_temp': 100,
                                                   'white_value': 50})

        with patch('homeassistant.components.light.mqtt_json'
                   '.async_get_last_state',
                   return_value=mock_coro(fake_state)):
            assert setup_component(self.hass, light.DOMAIN, {
                light.DOMAIN: {
                    'platform': 'mqtt_json',
                    'name': 'test',
                    'command_topic': 'test_light_rgb/set',
                    'brightness': True,
                    'color_temp': True,
                    'effect': True,
                    'rgb': True,
                    'white_value': True,
                    'qos': 2
                }
            })

        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert 95 == state.attributes.get('brightness')
        assert (100, 100) == state.attributes.get('hs_color')
        assert 'random' == state.attributes.get('effect')
        assert 100 == state.attributes.get('color_temp')
        assert 50 == state.attributes.get('white_value')
        assert 191 == state.attributes.get(ATTR_SUPPORTED_FEATURES)
        assert state.attributes.get(ATTR_ASSUMED_STATE)

        common.turn_on(self.hass, 'light.test')
        self.hass.block_till_done()

        self.mock_publish.async_publish.assert_called_once_with(
            'test_light_rgb/set', '{"state": "ON"}', 2, False)
        self.mock_publish.async_publish.reset_mock()
        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state

        common.turn_off(self.hass, 'light.test')
        self.hass.block_till_done()

        self.mock_publish.async_publish.assert_called_once_with(
            'test_light_rgb/set', '{"state": "OFF"}', 2, False)
        self.mock_publish.async_publish.reset_mock()
        state = self.hass.states.get('light.test')
        assert STATE_OFF == state.state

        common.turn_on(self.hass, 'light.test',
                       brightness=50, color_temp=155, effect='colorloop',
                       white_value=170)
        self.hass.block_till_done()

        assert 'test_light_rgb/set' == \
            self.mock_publish.async_publish.mock_calls[0][1][0]
        assert 2 == \
            self.mock_publish.async_publish.mock_calls[0][1][2]
        assert self.mock_publish.async_publish.mock_calls[0][1][3] is False
        # Get the sent message
        message_json = json.loads(
            self.mock_publish.async_publish.mock_calls[0][1][1])
        assert 50 == message_json["brightness"]
        assert 155 == message_json["color_temp"]
        assert 'colorloop' == message_json["effect"]
        assert 170 == message_json["white_value"]
        assert "ON" == message_json["state"]

        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert 50 == state.attributes['brightness']
        assert 155 == state.attributes['color_temp']
        assert 'colorloop' == state.attributes['effect']
        assert 170 == state.attributes['white_value']

        # Test a color command
        common.turn_on(self.hass, 'light.test',
                       brightness=50, hs_color=(125, 100))
        self.hass.block_till_done()

        assert 'test_light_rgb/set' == \
            self.mock_publish.async_publish.mock_calls[0][1][0]
        assert 2 == \
            self.mock_publish.async_publish.mock_calls[0][1][2]
        assert self.mock_publish.async_publish.mock_calls[0][1][3] is False
        # Get the sent message
        message_json = json.loads(
            self.mock_publish.async_publish.mock_calls[1][1][1])
        assert 50 == message_json["brightness"]
        assert {
            'r': 0,
            'g': 255,
            'b': 21,
        } == message_json["color"]
        assert "ON" == message_json["state"]

        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert 50 == state.attributes['brightness']
        assert (125, 100) == state.attributes['hs_color']

    def test_sending_hs_color(self):
        """Test light.turn_on with hs color sends hs color parameters."""
        assert setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {
                'platform': 'mqtt_json',
                'name': 'test',
                'command_topic': 'test_light_rgb/set',
                'hs': True,
            }
        })

        common.turn_on(self.hass, 'light.test', hs_color=(180.0, 50.0))
        self.hass.block_till_done()

        message_json = json.loads(
            self.mock_publish.async_publish.mock_calls[0][1][1])
        assert "ON" == message_json["state"]
        assert {
            'h': 180.0,
            's': 50.0,
        } == message_json["color"]

    def test_flash_short_and_long(self):
        """Test for flash length being sent when included."""
        assert setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {
                'platform': 'mqtt_json',
                'name': 'test',
                'state_topic': 'test_light_rgb',
                'command_topic': 'test_light_rgb/set',
                'flash_time_short': 5,
                'flash_time_long': 15,
                'qos': 0
            }
        })

        state = self.hass.states.get('light.test')
        assert STATE_OFF == state.state
        assert 40 == state.attributes.get(ATTR_SUPPORTED_FEATURES)

        common.turn_on(self.hass, 'light.test', flash="short")
        self.hass.block_till_done()

        assert 'test_light_rgb/set' == \
            self.mock_publish.async_publish.mock_calls[0][1][0]
        assert 0 == \
            self.mock_publish.async_publish.mock_calls[0][1][2]
        assert self.mock_publish.async_publish.mock_calls[0][1][3] is False
        # Get the sent message
        message_json = json.loads(
            self.mock_publish.async_publish.mock_calls[0][1][1])
        assert 5 == message_json["flash"]
        assert "ON" == message_json["state"]

        self.mock_publish.async_publish.reset_mock()
        common.turn_on(self.hass, 'light.test', flash="long")
        self.hass.block_till_done()

        assert 'test_light_rgb/set' == \
            self.mock_publish.async_publish.mock_calls[0][1][0]
        assert 0 == \
            self.mock_publish.async_publish.mock_calls[0][1][2]
        assert self.mock_publish.async_publish.mock_calls[0][1][3] is False
        # Get the sent message
        message_json = json.loads(
            self.mock_publish.async_publish.mock_calls[0][1][1])
        assert 15 == message_json["flash"]
        assert "ON" == message_json["state"]

    def test_transition(self):
        """Test for transition time being sent when included."""
        assert setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {
                'platform': 'mqtt_json',
                'name': 'test',
                'state_topic': 'test_light_rgb',
                'command_topic': 'test_light_rgb/set',
                'qos': 0
            }
        })

        state = self.hass.states.get('light.test')
        assert STATE_OFF == state.state
        assert 40 == state.attributes.get(ATTR_SUPPORTED_FEATURES)

        common.turn_on(self.hass, 'light.test', transition=10)
        self.hass.block_till_done()

        assert 'test_light_rgb/set' == \
            self.mock_publish.async_publish.mock_calls[0][1][0]
        assert 0 == \
            self.mock_publish.async_publish.mock_calls[0][1][2]
        assert self.mock_publish.async_publish.mock_calls[0][1][3] is False
        # Get the sent message
        message_json = json.loads(
            self.mock_publish.async_publish.mock_calls[0][1][1])
        assert 10 == message_json["transition"]
        assert "ON" == message_json["state"]

        # Transition back off
        common.turn_off(self.hass, 'light.test', transition=10)
        self.hass.block_till_done()

        assert 'test_light_rgb/set' == \
            self.mock_publish.async_publish.mock_calls[1][1][0]
        assert 0 == \
            self.mock_publish.async_publish.mock_calls[1][1][2]
        assert self.mock_publish.async_publish.mock_calls[1][1][3] is False
        # Get the sent message
        message_json = json.loads(
            self.mock_publish.async_publish.mock_calls[1][1][1])
        assert 10 == message_json["transition"]
        assert "OFF" == message_json["state"]

    def test_brightness_scale(self):
        """Test for brightness scaling."""
        assert setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {
                'platform': 'mqtt_json',
                'name': 'test',
                'state_topic': 'test_light_bright_scale',
                'command_topic': 'test_light_bright_scale/set',
                'brightness': True,
                'brightness_scale': 99
            }
        })

        state = self.hass.states.get('light.test')
        assert STATE_OFF == state.state
        assert state.attributes.get('brightness') is None
        assert not state.attributes.get(ATTR_ASSUMED_STATE)

        # Turn on the light
        fire_mqtt_message(self.hass, 'test_light_bright_scale',
                          '{"state":"ON"}')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert 255 == state.attributes.get('brightness')

        # Turn on the light with brightness
        fire_mqtt_message(self.hass, 'test_light_bright_scale',
                          '{"state":"ON",'
                          '"brightness": 99}')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert 255 == state.attributes.get('brightness')

    def test_invalid_color_brightness_and_white_values(self):
        """Test that invalid color/brightness/white values are ignored."""
        assert setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {
                'platform': 'mqtt_json',
                'name': 'test',
                'state_topic': 'test_light_rgb',
                'command_topic': 'test_light_rgb/set',
                'brightness': True,
                'rgb': True,
                'white_value': True,
                'qos': '0'
            }
        })

        state = self.hass.states.get('light.test')
        assert STATE_OFF == state.state
        assert 185 == state.attributes.get(ATTR_SUPPORTED_FEATURES)
        assert state.attributes.get('rgb_color') is None
        assert state.attributes.get('brightness') is None
        assert state.attributes.get('white_value') is None
        assert not state.attributes.get(ATTR_ASSUMED_STATE)

        # Turn on the light
        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"color":{"r":255,"g":255,"b":255},'
                          '"brightness": 255,'
                          '"white_value": 255}')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert (255, 255, 255) == state.attributes.get('rgb_color')
        assert 255 == state.attributes.get('brightness')
        assert 255 == state.attributes.get('white_value')

        # Bad color values
        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"color":{"r":"bad","g":"val","b":"test"}}')
        self.hass.block_till_done()

        # Color should not have changed
        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert (255, 255, 255) == state.attributes.get('rgb_color')

        # Bad brightness values
        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"brightness": "badValue"}')
        self.hass.block_till_done()

        # Brightness should not have changed
        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert 255 == state.attributes.get('brightness')

        # Bad white value
        fire_mqtt_message(self.hass, 'test_light_rgb',
                          '{"state":"ON",'
                          '"white_value": "badValue"}')
        self.hass.block_till_done()

        # White value should not have changed
        state = self.hass.states.get('light.test')
        assert STATE_ON == state.state
        assert 255 == state.attributes.get('white_value')

    def test_default_availability_payload(self):
        """Test availability by default payload with defined topic."""
        assert setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {
                'platform': 'mqtt_json',
                'name': 'test',
                'state_topic': 'test_light_rgb',
                'command_topic': 'test_light_rgb/set',
                'availability_topic': 'availability-topic'
            }
        })

        state = self.hass.states.get('light.test')
        assert STATE_UNAVAILABLE == state.state

        fire_mqtt_message(self.hass, 'availability-topic', 'online')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_UNAVAILABLE != state.state

        fire_mqtt_message(self.hass, 'availability-topic', 'offline')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_UNAVAILABLE == state.state

    def test_custom_availability_payload(self):
        """Test availability by custom payload with defined topic."""
        assert setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {
                'platform': 'mqtt_json',
                'name': 'test',
                'state_topic': 'test_light_rgb',
                'command_topic': 'test_light_rgb/set',
                'availability_topic': 'availability-topic',
                'payload_available': 'good',
                'payload_not_available': 'nogood'
            }
        })

        state = self.hass.states.get('light.test')
        assert STATE_UNAVAILABLE == state.state

        fire_mqtt_message(self.hass, 'availability-topic', 'good')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_UNAVAILABLE != state.state

        fire_mqtt_message(self.hass, 'availability-topic', 'nogood')
        self.hass.block_till_done()

        state = self.hass.states.get('light.test')
        assert STATE_UNAVAILABLE == state.state


async def test_discovery_removal(hass, mqtt_mock, caplog):
    """Test removal of discovered mqtt_json lights."""
    await async_start(hass, 'homeassistant', {})
    data = (
        '{ "name": "Beer",'
        '  "platform": "mqtt_json",'
        '  "command_topic": "test_topic" }'
    )
    async_fire_mqtt_message(hass, 'homeassistant/light/bla/config',
                            data)
    await hass.async_block_till_done()
    state = hass.states.get('light.beer')
    assert state is not None
    assert state.name == 'Beer'
    async_fire_mqtt_message(hass, 'homeassistant/light/bla/config',
                            '')
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    state = hass.states.get('light.beer')
    assert state is None
