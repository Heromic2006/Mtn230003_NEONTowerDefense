# Neon Tower Defense

## Repository
https://github.com/Heromic2006/Mtn230003_NEONTowerDefense.git

## Description
Neon Tower Defense is a 2D interactive strategy game built in Python using pygame, where players place towers to defend against waves of enemies. The project is relevant to digital arts & media through its focus on visual design, animation, and interactive gameplay systems.

## Features
- Enemy Pathing System
	- Enemies will follow a path using coordinates, moving smoothly across the screen toward the goal.
- Tower Placement System
	- The player will use mouse input to place towers on valid areas of the map, with placement restricted based on available currency.
- Automatic Targeting & Shooting
	- Towers will detect enemies within range and automatically shoot projectiles at the nearest target.
- Projectile & Collision System
	- Bullets will move toward enemies and apply damage upon collision using hit detection logic.
- Wave System
	- Enemies will spawn in waves with increasing difficulty by adjusting speed, health, and quantity.
- Currency System
	- Players earn currency by defeating enemies and spend it to place additional towers.
- Health & Game Over System
	- The player loses health when enemies reach the end of the path, ending the game when health reaches zero.
- Visual Effects (Polish Feature)
	- Particle effects and neon-style visuals will be used to enhance feedback and overall aesthetic quality.

## Challenges
- Learning how to implement enemy pathing using waypoints instead of simple movement.
- Designing a system for towers to detect and target enemies efficiently.
- Managing multiple interacting objects (enemies, towers, bullets) in real time without performance issues.

## Outcomes
Ideal Outcome:
- A fully polished tower defense game with multiple tower types, smooth animations, particle effects, and progressively challenging waves.

Minimal Viable Outcome:
- A functional game where enemies follow a path, towers can be placed, and basic shooting and collision systems work correctly.

## Milestones

- Week 1
  1. Set up pygame window and game loop
  2. Implement enemy movement along a path

- Week 2
  1. Add tower placement system
  2. Implement shooting and collision detection

- Week 3
  1. Add wave system and difficulty scaling
  2. Implement currency and health systems

- Week 4 (Final)
  1. Add visual polish (effects, colors, UI)
  2. Fix bugs and prepare demo video
