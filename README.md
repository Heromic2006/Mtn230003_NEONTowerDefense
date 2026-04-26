# Mtn230003_NEONTowerDefense

pip install -r requirements.txt
python src/project.py

Neon Tower defense

Demo:

Links
GitHub Repo: https://github.com/Heromic2006/Mtn230003_NEONTowerDefense.git
Video: https://youtu.be/Ul8KuhcLmPY

Description:
Neon tower defense is a 2d strategy game built using Python and the pygame library. The objective is to defend against waves of enemies by placing defense towers along the map. Each tower will automatially detect and attack enemies within range, while the player manages resourses and health to survive

The project demonstrates programing concepts such as object-oriented design, real time game loops, event handling, and collision detection. Enemies follow a predefined path using waypoint based movement while towers use a targeting logic to attack the closest enemies.

The repository is organzed with the main game logic in src/project.py. This file contains the main game loop along with enemy, tower, and projectile classes. Additional systems such as wave spawning, currency managment, and health are also managed here

Design considerations included balancing performance with how many loaded and interacting objects their are and ensuring smooth gameplay. The use of object oriented programming helped in managing these interactions

future improvements could include
- more tower types
- enhanced visuals/audio
- a more advanced user interface

