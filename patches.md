# Patches v1

## Input.cpp
- getCombination is not bindable ?
- makeCombination is not bindable ?
## Script.cpp
- Add include Scene/Scene.hpp
## Utils.cpp
- replaceInPlace is not bindable ?
## System.cpp
- Add include Triggers/TriggerManager.hpp
- pollEvent is not bindable ?
- draw is not bindable ?
## Animator.cpp
- setTarget is not bindable ?
## Transform.cpp
- Init is not bindable ?
- to is not bindable ?
## Types.cpp
- ProtectedIdentifiable is not bindable ?

# Patches v2
## Transform.cpp
- Rebind to
## Engine.cpp
- Fix constobe to const obe
## Scene.cpp
- futureLoadFromFile is not correctly bound to loadFromFile ?
## Audio.cpp
- Format file or you'll get Rect.inl error
## System.cpp
- Format file or you'll get Rect.inl error
## Shapes.cpp
- Remove missing methods from Text
## GENERAL
- Reorder copy parents to avoid method override (Sprite:setPosition with Movable and Rect)

# Patches v3
## Transform.cpp
- Fix bad Referential::Axis name
## Types.cpp
- Add missing getId on ProtectedIdentifiable

# Patches v4
## Types.cpp
- Remove constructors for ProtectedIdentifiable since there is no accessible default constructor
## vili/parser.cpp
- error.raise_on_failure and error.message are being exposed but they should not be because they are templated attributes
- parser.error_message is being exposed but all its defintions are being flagged as nobind
- node.push is being exposed but doesn't like the move (&&), add proxy for this method
## Event.cpp
- EventGroup.get does have a templated method in its overload (same for EventGroupView)
## Canvas.cpp
- CanvasPositionable /forceabstract flag is not working
## Events/Actions.cpp
- Default constructor not usable
## Events/Keys.cpp
- Default constructor not usable