from pico2d import *

import random
import math
import game_framework
import game_world
from behavior_tree import BehaviorTree, Action, Sequence, Condition, Selector
import play_mode
import boy


# zombie Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# zombie Action Speed
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk', 'Idle']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images == None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image("./zombie/" + name + " (%d)" % i + ".png") for i in range(1, 11)]
            Zombie.font = load_font('ENCR10B.TTF', 40)
            Zombie.marker_image = load_image('hand_arrow.png')


    def __init__(self, x=None, y=None):
        self.x = x if x else random.randint(100, 1180)
        self.y = y if y else random.randint(100, 924)
        self.load_images()
        self.dir = 0.0      # radian 값으로 방향을 표시
        self.speed = 0.0
        self.frame = random.randint(0, 9)
        self.state = 'Idle'
        self.ball_count = 0
        self.tx, self.ty = 0, 0
        self.build_behavior_tree()

        self.patrol_locations = [(43, 274), (1118, 274), (1050, 494), (235, 991), (575,804),(1050,454),(1118,274)]
        self.loc_no = 0

    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50


    def update(self):
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        self.ht.run()
        # fill here


    def draw(self):
        if math.cos(self.dir) < 0:
            Zombie.images[self.state][int(self.frame)].composite_draw(0, 'h', self.x, self.y, 100, 100)
        else:
            Zombie.images[self.state][int(self.frame)].draw(self.x, self.y, 100, 100)
        self.font.draw(self.x - 10, self.y + 60, f'{self.ball_count}', (0, 0, 255))
        draw_rectangle(*self.get_bb())
        Zombie.marker_image.draw(self.tx - 25, self.ty - 25)

    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        if group == 'zombie:ball':
            self.ball_count += 1


    def set_target_location(self, x=None, y=None):
        self.tx, self.ty = x
        return BehaviorTree.SUCCESS


    def distance_less_than(self, x1, y1, x2, y2, r):
        distance2 = (x1-x2) ** 2 + (y1-y2) ** 2
        return distance2 < (PIXEL_PER_METER * r) ** 2
        pass

    def move_slightly_to(self, tx, ty):
        self.dir = math.atan2(ty-self.y, tx-self.x)
        # 이동하기위해 속도와 시간이 필요
        distance = RUN_SPEED_PPS * game_framework.frame_time
        self.x += distance * math.cos(self.dir)
        self.y += distance * math.sin(self.dir)


    def move_to(self, r=0.5):
        self.state = 'Walk'
        self.move_slightly_to(self.tx, self.ty)
        if self.distance_less_than(self.tx, self.ty, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING
    def set_random_location(self):
        self.tx, self.ty = random.randint(100, 1280 - 100), random.randint(100, 1024 - 100)
        return BehaviorTree.SUCCESS

    def is_boy_nearby(self, r):
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL

    def move_to_boy(self, r=0.5):
        self.state = 'Walk'
        self.move_slightly_to(play_mode.boy.x, play_mode.boy.y)
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, r):
            return  BehaviorTree.SUCCESS
        else:
            return  BehaviorTree.RUNNING

    # def get_patrol_location(self):
    #     self.tx, self.ty = self.patrol_locations[self.loc_no]
    #     self.loc_no = (self.loc_no+1) % len(self.patrol_locations)
    #     return BehaviorTree.SUCCESS

    def compare_ball_1(self):
        if play_mode.boy.ball_count <= self.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL
    def compare_ball_2(self):
        if play_mode.boy.ball_count > self.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL

    def is_within_7_meters(self):
        """소년과의 거리가 7미터 이내인지 확인"""
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, 7):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL

    def move_away_from_boy(self):
        """소년과 반대 방향으로 이동"""
        self.state = 'Walk'
        # 반대 방향 계산
        direction = math.atan2(self.y - play_mode.boy.y, self.x - play_mode.boy.x)
        distance = RUN_SPEED_PPS * game_framework.frame_time
        self.x += distance * math.cos(direction)
        self.y += distance * math.sin(direction)

        # 이동 후 완료
        return BehaviorTree.SUCCESS

    def build_behavior_tree(self):
        # 7미터 이내 조건
        c1 = Condition('소년이 7미터 이내인가?', self.is_within_7_meters)

        # 공 비교 조건
        c2 = Condition('공 개수가 소년보다 같거나 많다', self.compare_ball_1)
        c3 = Condition('공 개수가 소년보다 적다', self.compare_ball_2)

        # 행동 정의
        a1 = Action("Set random location", self.set_random_location)
        a2 = Action('Move to', self.move_to)
        a3 = Action('소년한테 접근', self.move_to_boy)
        a4 = Action('반대 방향으로 이동', self.move_away_from_boy)

        # 7미터 안에서의 행동
        chase_boy = Sequence('공 비교 후 추적', c2, a3)
        flee = Sequence('공 비교 후 반대 방향 도망', c3, a4)
        chase_or_flee = Selector('추적 또는 반대 방향 도망', chase_boy, flee)

        # 7미터 밖에서의 행동
        wander = Sequence('배회', a1, a2)

        # 7미터 조건에 따른 행동 선택
        within_7_meters = Sequence('7미터 안에서 행동', c1, chase_or_flee)
        outside_7_meters = Sequence('7미터 밖에서 배회', wander)

        # 최종 트리: 7미터 조건에 따라 행동 선택
        root = Selector('7미터 조건 행동 선택', within_7_meters, outside_7_meters)

        self.ht = BehaviorTree(root)



