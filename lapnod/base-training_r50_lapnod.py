# ============================= model =======================
# model settings
norm_cfg = dict(type='BN', requires_grad=False)
pretrained = 'open-mmlab://detectron2/resnet50_caffe'
num_classes = 1
classes = 'BASE_CLASSES_SPLIT1'
model = dict(
    type='ICPE',
    pretrained=pretrained,
    backbone=dict(
        type='ResNetWithMetaConv',
        depth=50,
        num_stages=3,
        strides=(1, 2, 2, ),
        dilations=(1, 1, 1, ),
        out_indices=(2, ),
        frozen_stages=1,
        norm_cfg=norm_cfg,
        norm_eval=True,
        style='caffe'),
    information_coupling=dict(
        type='ConditionalInformationCouplingModule',
        in_channels=1024,
        inter_channels=1024,
        dimension=2,
        sub_sample=False,
        bn_layer=True),
    rpn_head=dict(
        type='RPNHead',
        in_channels=1024,
        feat_channels=512,
        anchor_generator=dict(
            type='AnchorGenerator',
            scales=[2, 4, 8, 16, 32],
            ratios=[0.5, 1.0, 2.0],
            scale_major=False,
            strides=[16]),
        bbox_coder=dict(
            type='DeltaXYWHBBoxCoder',
            target_means=[.0, .0, .0, .0],
            target_stds=[1.0, 1.0, 1.0, 1.0]),
        loss_cls=dict(
            type='CrossEntropyLoss', use_sigmoid=False, loss_weight=1.0),
        loss_bbox=dict(type='L1Loss', loss_weight=1.0)),
    roi_head=dict(
        type='ICPERoIHead',
        shared_head=dict(
            type='MetaRCNNResLayer',
            pretrained=pretrained,
            depth=50,
            stage=3,
            stride=2,
            dilation=1,
            style='caffe',
            norm_cfg=norm_cfg,
            norm_eval=True),
        bbox_roi_extractor=dict(
            type='SingleRoIExtractor',
            roi_layer=dict(type='RoIAlign', output_size=14, sampling_ratio=0),
            out_channels=1024,
            featmap_strides=[16]),
        bbox_head=dict(
            type='MetaBBoxHead',
            with_avg_pool=False,
            roi_feat_size=1,
            in_channels=2048,
            num_classes=num_classes,
            num_meta_classes=num_classes,
            meta_cls_in_channels=2048,
            with_meta_cls_loss=True,
            bbox_coder=dict(
                type='DeltaXYWHBBoxCoder',
                target_means=[0., 0., 0., 0.],
                target_stds=[0.1, 0.1, 0.2, 0.2]),
            reg_class_agnostic=False,
            loss_meta=dict(
                type='CrossEntropyLoss', use_sigmoid=False, loss_weight=1.0),
            loss_cls=dict(
                type='CrossEntropyLoss', use_sigmoid=False, loss_weight=1.0),
            loss_bbox=dict(type='SmoothL1Loss', loss_weight=1.0)),
        support_without_mean=True,
        prototype_aggregation=dict(
            type='PrototypeDynamicAggregation',
            in_channels=2048,
            alpha=1.0
        ),
        aggregation_layer=dict(
            type='AggregationLayer',
            aggregator_cfgs=[
                dict(
                    type='DotProductAggregator',
                    in_channels=2048,
                    with_fc=False)
            ])),
    # model training and testing settings
    train_cfg=dict(
        rpn=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                pos_iou_thr=0.7,
                neg_iou_thr=0.3,
                min_pos_iou=0.3,
                match_low_quality=True,
                ignore_iof_thr=-1),
            sampler=dict(
                type='RandomSampler',
                num=256,
                pos_fraction=0.5,
                neg_pos_ub=-1,
                add_gt_as_proposals=False),
            allowed_border=0,
            pos_weight=-1,
            debug=False),
        rpn_proposal=dict(
            nms_pre=12000,
            max_per_img=2000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                pos_iou_thr=0.5,
                neg_iou_thr=0.5,
                min_pos_iou=0.5,
                match_low_quality=False,
                ignore_iof_thr=-1),
            sampler=dict(
                type='RandomSampler',
                num=128,
                pos_fraction=0.25,
                neg_pos_ub=-1,
                add_gt_as_proposals=True),
            pos_weight=-1,
            debug=False)),
    test_cfg=dict(
        rpn=dict(
            nms_pre=6000,
            max_per_img=300,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=dict(
            score_thr=0.05,
            nms=dict(type='nms', iou_threshold=0.3),
            max_per_img=100)))


# ============================= dataset =======================
# dataset settings
img_norm_cfg = dict(
    mean=[123.653, 123.653, 123.653], std=[1.0, 1.0, 1.0], to_rgb=False)
train_multi_pipelines = dict(
    query=[
        dict(type='LoadImageFromFile'),
        dict(type='LoadAnnotations', with_bbox=True),
        dict(
             type='Resize',
             img_scale=[(1333, 480), (1333, 512), (1333, 544), (1333, 576),
                        (1333, 608), (1333, 640), (1333, 672), (1333, 704),
                        (1333, 736), (1333, 768), (1333, 800), (1333, 1024), (1333, 1280)],
             keep_ratio=True,
             multiscale_mode='value'),
        dict(type='RandomFlip', flip_ratio=0.5),
        dict(type='Normalize', **img_norm_cfg),
        dict(type='DefaultFormatBundle'),
        dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels'])
    ],
    support=[
        dict(type='LoadImageFromFile'),
        dict(type='LoadAnnotations', with_bbox=True),
        dict(type='Normalize', **img_norm_cfg),
        dict(type='GenerateMask', target_size=(224, 224)),
        dict(type='RandomFlip', flip_ratio=0.0),
        dict(type='DefaultFormatBundle'),
        dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels'])
    ])
test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(1333, 1280),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img'])
        ])
]
# classes splits are predefined in FewShotVOCDataset
data_root = 'data/VOCdevkit/'
data = dict(
    samples_per_gpu=4,
    workers_per_gpu=4,
    train=dict(
        type='NWayKShotDataset',
        num_support_ways=1,
        num_support_shots=20,
        one_support_shot_per_image=True,
        num_used_support_shots=600,
        save_dataset=False,
        dataset=dict(
            type='FewShotVOCDataset',
            ann_cfg=[
                dict(
                    type='ann_file',
                    ann_file=data_root + 'VOC2007/ImageSets/Main/train.txt')
            ],
            img_prefix=data_root,
            multi_pipelines=train_multi_pipelines,
            classes=classes,
            use_difficult=True,
            instance_wise=False,
            dataset_name='query_dataset'),
        support_dataset=dict(
            type='FewShotVOCDataset',
            ann_cfg=[
                dict(
                    type='ann_file',
                    ann_file=data_root + 'VOC2007/ImageSets/Main/train.txt')
            ],
            img_prefix=data_root,
            multi_pipelines=train_multi_pipelines,
            classes=classes,
            use_difficult=False,
            instance_wise=False,
            dataset_name='support_dataset')),
    val=dict(
        type='FewShotVOCDataset',
        ann_cfg=[
            dict(
                type='ann_file',
                ann_file=data_root + 'VOC2007/ImageSets/Main/val_lapnod.txt')
        ],
        img_prefix=data_root,
        pipeline=test_pipeline,
        classes=classes),
    test=dict(
        type='FewShotVOCDataset',
        ann_cfg=[
            dict(
                type='ann_file',
                ann_file=data_root + 'VOC2007/ImageSets/Main/val_lapnod.txt')
        ],
        img_prefix=data_root,
        pipeline=test_pipeline,
        test_mode=True,
        classes=classes),
    model_init=dict(
        copy_from_train_dataset=True,
        samples_per_gpu=16,
        workers_per_gpu=4,
        type='FewShotVOCDataset',
        ann_cfg=None,
        img_prefix=data_root,
        pipeline=train_multi_pipelines['support'],
        use_difficult=False,
        instance_wise=True,
        classes=classes,
        dataset_name='model_init_dataset'))
evaluation = dict(interval=100, metric='mAP')


# ============================= schedule =======================
# optimizer
optimizer = dict(type='SGD', lr=0.005, momentum=0.9, weight_decay=0.0001)
optimizer_config = dict(grad_clip=None)
# learning policy
lr_config = dict(
    policy='step',
    warmup='linear',
    warmup_iters=400,
    warmup_ratio=0.001,
    step=[6000, 8000])
runner = dict(type='IterBasedRunner', max_iters=9000)

# ============================= default =======================
checkpoint_config = dict(interval=500)
# yapf:disable
log_config = dict(
    interval=50,
    hooks=[
        dict(type='TextLoggerHook'),
        # dict(type='TensorboardLoggerHook')
    ])
# yapf:enable
custom_hooks = [dict(type='NumClassCheckHook')]

dist_params = dict(backend='nccl')
log_level = 'INFO'
#load_from = '/share1/home/wbq/lcl/code/mmdetection/weights/resim_backbone.pth'
#load_from = '/share1/home/wbq/lcl/code/ReSim/weights/resim_200+200_icpe.pth'

load_from = None
resume_from = None
workflow = [('train', 1)]
use_infinite_sampler = True
# a magical seed works well in most cases for this repo!!!
# using different seeds might raise some issues about reproducibility
seed = 42
work_dir = './results/base_r50'

