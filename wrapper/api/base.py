# -*- coding: utf-8 -*-


import time

import core.exceptions as exceptions

from api.minecraft import Minecraft
from api.util import Utils
from core.storage import Storage
from api.backups import Backups


# noinspection PyPep8Naming
class API:
    """
    The API class contains methods for basic plugin functionality, such as handling events,
    registering commands, and more. Most methods aren't related to gameplay, aside from commands
    and events, but for core stuff. See the Minecraft class (accessible at self.api.minecraft)
    for gameplay-related methods.

    :sample usage:


.. code:: python

    class Main:
        def __init__(self, api, log):
            self.api = api

        def onEnable(self):
            self.api.minecraft.registerHelp("Home", "Commands from the Home plugin", [
                ("/sethome", "Save curremt position as home", None),
                ("/home", "Teleports you to your home set by /sethome", None),
            ])

            self.api.minecraft.registerCommand("sethome", self.sethome)
..


    """
    statuseffects = {
        "speed": 1,
        "slowness": 2,
        "haste": 3,
        "mining_fatigue": 4,
        "strength": 5,
        "instant_health": 6,
        "instant_damage": 7,
        "jump_boost": 8,
        "nausea": 9,
        "regeneration": 10,
        "resistance": 11,
        "fire_resistance": 12,
        "water_breathing": 13,
        "invisibility": 14,
        "blindness": 15,
        "night_vision": 16,
        "hunger": 17,
        "weakness": 18,
        "poison": 19,
        "wither": 20,
        "health_boost": 21,
        "absorption": 22,
        "saturation": 23
    }
    colorcodes = {
        "0": "black",
        "1": "dark_blue",
        "2": "dark_green",
        "3": "dark_aqua",
        "4": "dark_red",
        "5": "dark_purple",
        "6": "gold",
        "7": "gray",
        "8": "dark_gray",
        "9": "blue",
        "a": "green",
        "b": "aqua",
        "c": "red",
        "d": "light_purple",
        "e": "yellow",
        "f": "white",
        "r": "\xc2\xa7r",
        "k": "\xc2\xa7k",  # obfuscated
        "l": "\xc2\xa7l",  # bold
        "m": "\xc2\xa7m",  # strikethrough
        "n": "\xc2\xa7n",  # underline
        "o": "\xc2\xa7o",  # italic,
    }

    def __init__(self, wrapper, name="", someid=None, internal=False):
        self.wrapper = wrapper
        self.log = wrapper.log
        self.name = name
        self.minecraft = Minecraft(wrapper)
        self.backups = Backups(wrapper)
        self.utils = Utils()
        self.config = wrapper.config
        self.entity = False
        self.serverpath = self.config["General"]["server-directory"]
        self.internal = internal
        if someid is None:
            self.id = name
        else:
            self.id = someid

    def registerCommand(self, command, callback, permission=None):
        """
        This registers a command that, when entered by the Minecraft client, will execute `callback(player, args)`.
        permission is an optional attribute if you want your command to only be executable if the player
        has a specified permission node.

        :command:  The command the client enters (without the slash).  using a slash will mean two slashes will have
         to be typed (e.g. "/region" means the user must type "//region".

        :callback:  The plugin method you want to call the command is typed. Expected arguments are 1) the player
         object, 2) a list of the arguments (words after the command, stripped of whitespace).

        :permission:  A string item of your choosing, such as "essentials.home".  Can be (type) None to require no
         permission.  (See also `api.registerPermission` for another way to set permission defaults.)

        :sample usage:

        `self.api.registerCommand("home", self._home, None)`

        :returns:  None/Nothing

        """
        commands = []
        if type(command) in (tuple, list):
            for i in command:
                commands.append(i)
        else:
            commands = [command]
        for name in commands:
            if not self.internal:
                self.wrapper.log.debug("[%s] Registered command '%s'", self.name, name)
            if self.id not in self.wrapper.commands:
                self.wrapper.commands[self.id] = {}
            self.wrapper.commands[self.id][name] = {"callback": callback, "permission": permission}

    def registerEvent(self, eventname, callback):
        """
        Register an event and a callback function. See
         https://docs.google.com/spreadsheets/d/1Sxli0mpN3Aib-aejjX7VRlcN2HZkak_wIqPFJ6mtVIk/edit?usp=sharing
         for a list of events.

        :eventname:  A text name from the list of built-in events, for example, "player.place".

        :callback: the plugin method you want to be called when the event occurs. The contents of the payload that is
         passed back to your method varies between events.


        :returns:  None/Nothing

        """
        if not self.internal:
            self.wrapper.log.debug("[%s] Registered event '%s'", self.name, eventname)
        if self.id not in self.wrapper.events:
            self.wrapper.events[self.id] = {}
        self.wrapper.events[self.id][eventname] = callback

    def registerPermission(self, permission=None, value=False):
        """
        Used to set a default for a specific permission node.
        Note: You do not need to run this function unless you want certain permission nodes
        to be granted by default.  i.e. `essentials.list` should be on by default, so players
        can run /list without having any permissions.

        :permission:  String argument for the permission node; e.g. "essentials.list"

        :value:  Set to True to make a permission default to True.

        :returns:  None/Nothing

        """
        if not self.internal:
            self.wrapper.log.debug("[%s] Registered permission '%s' with default value: %s",
                                   self.name, permission, value)
        if self.id not in self.wrapper.registered_permissions:
            self.wrapper.registered_permissions[self.id] = {}
        self.wrapper.registered_permissions[self.id][permission] = value

    def registerHelp(self, groupname, summary, commands):
        """
        Used to create a help group for the /help command.

        :groupname: The name of the help group (usually the plugin name). The groupname is the name you'll see
         in the list when you run '/help'.

        :summary: The text that you'll see next next to the help group's name.

        :commands: a list of tuples in the following example format:

        [("/command <argument>, [optional_argument]", "description", "permission.node"),
         ("/summon <EntityName> [x] [y] [z]", "Summons an entity", None),
         ("/suicide", "Kills you - beware of losing your stuff!", "essentials.suicide")]

        :returns:  None/Nothing

        """
        if not self.internal:
            self.wrapper.log.debug("[%s] Registered help group '%s' with %d commands",
                                   self.name, groupname, len(commands))
        if self.id not in self.wrapper.help:
            self.wrapper.help[self.id] = {}
        self.wrapper.help[self.id][groupname] = (summary, commands)

    def blockForEvent(self, eventtype):
        # TODO this event's purpose/functionality and use cases are unknown at this time
        """
        Blocks until the specified event is called. """
        sock = []
        self.wrapper.events.listeners.append(sock)  #
        while True:
            for event in sock:
                if event["event"] == eventtype:
                    payload = event["payload"][:]
                    self.wrapper.events.listeners.remove(sock)
                    return payload
                else:
                    sock.remove(event)
            time.sleep(0.05)

    def callEvent(self, event, payload):
        # TODO this event's purpose/functionality and use cases are unknown at this time
        """
        Invokes the specific event. Payload is extra information relating to the event. Errors
        may occur if you don't specify the right payload information.
        """
        return self.wrapper.callevent(event, payload)

    def getPluginContext(self, plugin_id):
        """
        Returns the instance (content) of another running wrapper plugin with the specified ID.

        :plugin_id:  The `ID` of the plugin from the plugin's header .  if no `ID` was specified by the plugin, then
         the file name (without the .py extension) is used as the `ID`.

        :sample usage:

.. code:: python

        essentials_id = "com.benbaptist.plugins.essentials"
        running_essentials = api.getPluginContext(essentials_id)
        warps = running_essentials.data["warps"]
        print("Warps data currently being used by essentials: \\n %s" % warps)
..

        :returns:  Raises wrapper exception `exceptions.NonExistentPlugin` if the specified plugin does not exist.

"""
        if plugin_id in self.wrapper.plugins:
            return self.wrapper.plugins[plugin_id]["main"]
        else:
            raise exceptions.NonExistentPlugin("Plugin %s does not exist!" % plugin_id)

    def getStorage(self, name, world=False):
        """
        Return a storage object for storing configurations, player data, and any other data your
        plugin will need to remember across reboots.

        :name:  The name of the storage.

        :world:

         `False` sets the storages location to `/wrapper-data/plugins`.

         `True` sets the storage path to `<serverpath>/<worldname>/plugins`.

        :sample methods:

.. code:: python

        # to start a storage:
        self.data = self.api.getStorage("worldly", True)

        # to save:
        self.data.save()  # storages also do periodic saves every minute.

        # to close (and save):
        def onDisable(self):
            self.data.close()
..

        """
        if world:
            return Storage(name, root="%s/%s/plugins/%s" %
                                      (self.serverpath, self.minecraft.getWorldName(), self.id))
        else:
            return Storage(name, root="wrapper-data/plugins/%s" % self.id)

    def wrapperHalt(self):
        """
        Shuts wrapper down entirely.  To use this as a wrapper-restart method, use some code like this in a shell
        file to start wrapper (Linux example).  This code will restart wrapper after every shutdown until the
        console user ends it with CTRL-C.

.. caution::
    (using CTRL-C will allow Wrapper.py to close gracefully, saving it's Storages, and shutting down plugins.
    Don't use CTRL-Z unless absolutely necessary!)
..

./start.sh


.. code:: bash

        #! bin/bash
        function finish() {
          echo "Stopped startup script!"
          read -p "Press [Enter] key to continue..."
          exit
        }

        trap finish SIGINT SIGTERM SIGQUIT

        while true; do
          cd "/home/wrapper/"
          python Wrapper.py
          sleep 1
        done
..

        """
        self.wrapper.shutdown()