---@meta

---@type obe.Engine.Engine
Engine = {};

---@type obe.Script.GameObject
This = {};

---@type obe.Events._EventTable
Event = {};

---@type table<string, any>
Object = {};

---@type table<string, any>
Global = {};

---@type table<string, function>
Task = {};

Local = {};

--- GameObject constructor
function Local.Init()
end

--- GameObject destructor
function Local.Delete()
end

---@alias _EventHook userdata

--- Listen to an EventNamespace / EventGroup / Event
---
---@param listen_target string #ID of the EventNamespace / EventGroup / Event to listen to (eg. "Event.Game.Update")
---@param callback? function #Event Callback (only used if the target is an Event)
---@param listener_id? string #Optional Event listener id (defaults to __ENV_ID)
---@return _EventHook
function listen(listen_target, callback, listener_id)
end

--- Disables hook created with "listen" function
---
---@param hook _EventHook #Hook previously returned by "listen" function
function unlisten(hook)
end

--- Creates a new callback scheduler managed by the GameObject
---
---@return obe.Event.CallbackScheduler
function schedule()
end

return {Engine, This, Event, Object, Global, Task, Local, listen, unlisten, schedule}
