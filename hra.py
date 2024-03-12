import random
import pygame
import sys

player_image = pygame.image.load("player.png")
skret_image = pygame.image.load("skřet.png")
kostlivec_image = pygame.image.load("kostlivec.png")
zlymag_image = pygame.image.load("zlý_mág.png")
blob_image = pygame.image.load("blob.png")
blobik_image = pygame.image.load("blobik.png")
demon_image = pygame.image.load("démon.png")

COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 10
        self.strength = 3
        self.lives = 10
        self.kills = 0
        self.items_found = []
        self.rounds_played = 0
        self.spawn_chance = 0.5
        self.dodge_chance = 0
        self.max_armor = 10  # Maximální počet zbrojí
        self.current_armor = 0  # Aktuální počet zbrojí

    def move(self, dx, dy, enemies):
        new_x = self.x + dx
        new_y = self.y + dy

        if 0 <= new_x < 19 and 0 <= new_y < 19:
            target_enemy = next(
                (enemy for enemy in enemies if enemy.x == new_x and enemy.y == new_y),
                None,
            )
            if target_enemy:
                self.attack(target_enemy)
            else:
                self.x = new_x
                self.y = new_y

    def attack(self, enemy):
        enemy.health -= self.strength
        if enemy.health <= 0:
            enemy.alive = False
            self.kills += 1
            item_chance = random.random() * 100
            item_name = None
            if item_chance < 10:
                self.strength += 1
                item_name = "zbraň"
            elif 10 <= item_chance < 14:
                self.health += 3
                item_name = "léčivo"
            elif 14 <= item_chance < 18:
                if self.current_armor < self.max_armor:  # Kontrola maximálního počtu zbrojí
                    self.current_armor += 1
                    self.dodge_chance += 5
                    item_name = "zbroj"
            if item_name:
                self.items_found.append(item_name)
                self.display_message(item_name)

    def is_alive(self):
        return self.health > 0 and self.lives > 0

    def display_message(self, item_name):
        self.last_item_found = item_name

    def dodge_attack(self):
        return random.random() < self.dodge_chance / 100


class Enemy:
    def __init__(self, name, health, strength, x, y):
        self.name = name
        self.health = health
        self.strength = strength
        self.x = x
        self.y = y
        self.alive = True

    def move_towards_player(self, player, enemies):
        dx = player.x - self.x
        dy = player.y - self.y

        if abs(dx) > abs(dy):
            new_x = self.x + (1 if dx > 0 else -1)
            new_y = self.y
        else:
            new_x = self.x
            new_y = self.y + (1 if dy > 0 else -1)

        if 0 <= new_x < 19 and 0 <= new_y < 19:
            occupied = any(
                enemy.x == new_x and enemy.y == new_y for enemy in enemies
            ) or (player.x == new_x and player.y == new_y)
            if not occupied:
                self.x = new_x
                self.y = new_y
            else:
                self.find_alternate_path(player, enemies)

    def find_alternate_path(self, player, enemies):

        possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(possible_moves)

        for dx, dy in possible_moves:
            new_x = self.x + dx
            new_y = self.y + dy

            if 0 <= new_x < 19 and 0 <= new_y < 19:
                occupied = any(
                    enemy.x == new_x and enemy.y == new_y for enemy in enemies
                ) or (player.x == new_x and player.y == new_y)
                if not occupied:
                    self.x = new_x
                    self.y = new_y
                    return

    def attack(self, player):
        if not player.dodge_attack():
            player.health -= self.strength
        if player.health <= 0:
            player.lives -= 1
        self.alive = False if self.health <= 0 else True

    def is_alive(self):
        return self.health > 0


class Blob(Enemy):
    def __init__(self, x, y):
        super().__init__("blob", 6, 2, x, y)

    def spawn_small_blobs(self, enemies):

        free_spots = [
            (self.x + dx, self.y + dy) for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]
        ]
        for x, y in free_spots:
            if (0 <= x < 19 and 0 <= y < 19) and not any(
                enemy.x == x and enemy.y == y for enemy in enemies
            ):
                enemies.append(Blobik(x, y))


class Blobik(Enemy):
    def __init__(self, x, y):
        super().__init__("blobik", 3, 1, x, y)


class Demon(Enemy):
    demon_count = 0

    def __init__(self, x, y):
        super().__init__("démon", self.demon_count, 3, x, y)  # Síla démona závisí na počtu démonů

    def spawn(self):
        Demon.demon_count += 1

    def despawn(self):
        Demon.demon_count -= 1


def spawn_enemy(player, enemies, rounds_played):
    if rounds_played >= 60:
        enemy_types = ["kostlivec", "zlý mág", "blob", "démon"]
    elif rounds_played >= 30:
        enemy_types = ["skřet", "kostlivec", "zlý mág", "blob"]
    else:
        enemy_types = ["skřet", "kostlivec", "zlý mág"]

    if random.random() < player.spawn_chance:
        enemy_type = random.choice(enemy_types)
        if enemy_type == "skřet":
            return Enemy("skřet", 3, 1, random.randint(0, 18), random.randint(0, 18))
        elif enemy_type == "kostlivec":
            return Enemy(
                "kostlivec", 5, 1, random.randint(0, 18), random.randint(0, 18)
            )
        elif enemy_type == "zlý mág":
            return Enemy(
                "zlý mág", 2, 2, random.randint(0, 18), random.randint(0, 18)
            )
        elif enemy_type == "blob":
            return Blob(random.randint(0, 18), random.randint(0, 18))
        elif enemy_type == "démon":
            demon = Demon(random.randint(0, 18), random.randint(0, 18))
            demon.spawn()
            return demon


def adjust_spawn_chance(player):

    if player.rounds_played % 20 == 0:
        player.spawn_chance += 0.1


def draw_grid(screen):
    for y in range(0, 380, 20):
        for x in range(0, 380, 20):
            pygame.draw.rect(screen, (0, 0, 0), (x, y, 20, 20), 1)


def draw_player(screen, player, rounds_played):
    screen.blit(player_image, (player.x * 20, player.y * 20))
    font = pygame.font.SysFont(None, 20)
    text = font.render(
        f"Health: {player.health}, Kills: {player.kills}, Round: {rounds_played}",
        True,
        (255, 255, 255),
    )
    screen.blit(text, (10, 10))

    y_offset = 360
    items_to_display = {
        item: player.items_found.count(item) for item in set(player.items_found)
    }
    for item, count in items_to_display.items():
        if count > 1:
            item_text = f"{item} ({count})"
        else:
            item_text = f"{item}"
        item_text_surface = font.render(item_text, True, (255, 255, 255))
        screen.blit(item_text_surface, (10, y_offset))
        y_offset += 20

    if hasattr(player, "last_item_found") and player.last_item_found not in player.items_found[:-1]:
        item_text = f"Našel jsi: {player.last_item_found}!"
        item_text_surface = font.render(item_text, True, COLORS[0])
        screen.blit(item_text_surface, (10, 340))

    items_text = ", ".join(
        [f"{item} ({count})" for item, count in items_to_display.items()]
    )
    items_text_surface = font.render(
        f"Získané předměty: {items_text}", True, (255, 255, 255)
    )
    screen.blit(items_text_surface, (10, 360))


def draw_enemy(screen, enemy):
    if enemy.name == "skřet":
        screen.blit(skret_image, (enemy.x * 20, enemy.y * 20))
    elif enemy.name == "kostlivec":
        screen.blit(kostlivec_image, (enemy.x * 20, enemy.y * 20))
    elif enemy.name == "zlý mág":
        screen.blit(zlymag_image, (enemy.x * 20, enemy.y * 20))
    elif enemy.name == "blob":
        screen.blit(blob_image, (enemy.x * 20, enemy.y * 20))
    elif enemy.name == "blobik":
        screen.blit(blobik_image, (enemy.x * 20, enemy.y * 20))
    elif enemy.name == "démon":
        screen.blit(demon_image, (enemy.x * 20, enemy.y * 20))


def main():
    pygame.init()
    screen = pygame.display.set_mode((380, 380))
    clock = pygame.time.Clock()

    player = Player(9, 9)
    enemies = []
    player_turn = True

    while player.is_alive():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and player_turn:
                if event.key == pygame.K_w:
                    player.move(0, -1, enemies)
                elif event.key == pygame.K_a:
                    player.move(-1, 0, enemies)
                elif event.key == pygame.K_s:
                    player.move(0, 1, enemies)
                elif event.key == pygame.K_d:
                    player.move(1, 0, enemies)
                # Po pohybu hráče kontrolujeme, zda byl nepřítel poražen, a odstraníme ho z listu enemies
                enemies = [enemy for enemy in enemies if enemy.is_alive()]
                player_turn = False
                player.rounds_played += 1

        screen.fill((0, 0, 0))
        draw_grid(screen)
        draw_player(screen, player, player.rounds_played)

        for enemy in enemies:
            draw_enemy(screen, enemy)

        pygame.display.flip()

        if not player_turn:

            for enemy in enemies:
                if (
                    (enemy.x == player.x + 1 and enemy.y == player.y)
                    or (enemy.x == player.x - 1 and enemy.y == player.y)
                    or (enemy.y == player.y + 1 and enemy.x == player.x)
                    or (enemy.y == player.y - 1 and enemy.x == player.x)
                ):
                    enemy.attack(player)
                else:
                    enemy.move_towards_player(player, enemies)

            new_enemy = spawn_enemy(player, enemies, player.rounds_played)
            if new_enemy:
                enemies.append(new_enemy)

            for enemy in enemies:
                if isinstance(enemy, Blob) and not enemy.is_alive():
                    enemy.spawn_small_blobs(enemies)

            player_turn = True

        pygame.display.flip()
        clock.tick(30)

    print("Game Over")


if __name__ == "__main__":
    main()